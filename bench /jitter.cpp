// Measures wake-up jitter of a periodic task. Real numbers, no simulation.
// Same question AEGIS answers on QNX: how late is "on time"?
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <ctime>
#include <cerrno>
#include <vector>

static inline int64_t now_ns() {
  timespec ts{};
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return int64_t(ts.tv_sec) * 1'000'000'000LL + ts.tv_nsec;
}

int main() {
  constexpr int64_t period_ns = 1'000'000;  // 1 kHz control loop
  constexpr int iters = 5000;

  std::vector<int64_t> lateness;
  lateness.reserve(iters);

  int64_t target = now_ns() + period_ns;
  for (int i = 0; i < iters; ++i) {
    timespec ts{time_t(target / 1'000'000'000LL), long(target % 1'000'000'000LL)};
    while (clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &ts, nullptr) == EINTR) {}
    lateness.push_back(now_ns() - target);
    target += period_ns;
  }

  std::sort(lateness.begin(), lateness.end());
  auto at = [&](double q) { return lateness[size_t(q * (lateness.size() - 1))]; };

  // microseconds, two decimals
  std::printf("{\"samples\":%d,\"period_us\":%lld,\"min_us\":%.2f,\"p50_us\":%.2f,"
              "\"p99_us\":%.2f,\"max_us\":%.2f,\"hist\":[",
              iters, (long long)(period_ns / 1000), at(0.0) / 1000.0, at(0.50) / 1000.0,
              at(0.99) / 1000.0, at(1.0) / 1000.0);

  // 24-bucket histogram over [min, p99]
  const double lo = at(0.0), hi = at(0.99) > at(0.0) ? at(0.99) : at(0.0) + 1;
  int buckets[24] = {0};
  for (int64_t v : lateness) {
    int b = int((double(v) - lo) / (hi - lo) * 23.0);
    if (b < 0) b = 0;
    if (b > 23) b = 23;
    buckets[b]++;
  }
  for (int i = 0; i < 24; ++i) std::printf("%s%d", i ? "," : "", buckets[i]);
  std::printf("]}\n");
  return 0;
}
