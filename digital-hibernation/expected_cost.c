// SPDX-License-Identifier: GPL-2.0
#define EC_WINDOW_SIZE 16
#define EC_PENALTY_MULT 3

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/percpu.h>
#include <linux/cpuidle.h>

struct ec_cpu_state {
    u64 idle_dur[EC_WINDOW_SIZE];
    u8 head;
    u8 count;
};

static DEFINE_PER_CPU(struct ec_cpu_state, ec_cpu_data);

static int ec_select(struct cpuidle_device *dev, struct cpuidle_driver *drv, int index)
{
    return 0;
}

static void ec_reflect(struct cpuidle_device *dev, int index)
{
    struct ec_cpu_state *ec = this_cpu_ptr(&ec_cpu_data);
    u64 dur_ns = (u64)dev->last_residency * 1000ULL;
    ec->idle_dur[ec->head] = dur_ns;
    ec->head = (ec->head + 1) % EC_WINDOW_SIZE;
    if (ec->count < EC_WINDOW_SIZE)
        ec->count++;
}

static int ec_enable_device(struct cpuidle_device *dev)
{
    struct ec_cpu_state *ec = per_cpu_ptr(&ec_cpu_data, dev->cpu);
    memset(ec, 0, sizeof(*ec));
    return 0;
}

static struct cpuidle_governor expected_cost_governor = {
    .name = "expected_cost",
    .rating = 25,
    .select = ec_select,
    .reflect = ec_reflect,
    .enable_device = ec_enable_device,
};

static int __init ec_governor_init(void)
{
    return cpuidle_register_governor(&expected_cost_governor);
}

static void __exit ec_governor_exit(void)
{
    cpuidle_unregister_governor(&expected_cost_governor);
}

module_init(ec_governor_init);
module_exit(ec_governor_exit);

MODULE_AUTHOR("Abdullah");
MODULE_DESCRIPTION("Expected-Cost cpuidle governor - Digital Hibernation");
MODULE_LICENSE("GPL");