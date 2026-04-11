/*
 * PysiAdmin — native/sysinfo.c
 * Outputs system metrics as JSON to stdout.
 * Build: make -C native
 * Use:   ./native/sysinfo
 */

#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/utsname.h>
#include <sys/sysinfo.h>
#include <sys/statvfs.h>

/* SI_LOAD_SHIFT is defined in <linux/sysinfo.h> but sysinfo(2) guarantees
   the shift is 16 on Linux.  Use it directly to stay header-agnostic.    */
#define LOAD_SHIFT 16

int main(void)
{
    struct utsname   uts  = {0};
    struct sysinfo   si   = {0};
    struct statvfs   vfs  = {0};
    char             host[256] = {0};

    if (uname(&uts)                  != 0) { perror("uname");     return 1; }
    if (sysinfo(&si)                 != 0) { perror("sysinfo");   return 1; }
    if (gethostname(host, sizeof host) != 0) { perror("hostname"); return 1; }
    /* non-fatal — disk info just shows 0 if / is unavailable */
    statvfs("/", &vfs);

    unsigned long total_ram_mb = (si.totalram * (unsigned long)si.mem_unit) >> 20;
    unsigned long free_ram_mb  = (si.freeram  * (unsigned long)si.mem_unit) >> 20;
    double        disk_total   = (double)(vfs.f_blocks * vfs.f_frsize) / (1024.0*1024.0*1024.0);
    double        disk_free    = (double)(vfs.f_bfree  * vfs.f_frsize) / (1024.0*1024.0*1024.0);
    double        load_scale   = 1.0 / (1 << LOAD_SHIFT);

    printf("{\n"
           "  \"hostname\":      \"%s\",\n"
           "  \"sysname\":       \"%s\",\n"
           "  \"release\":       \"%s\",\n"
           "  \"machine\":       \"%s\",\n"
           "  \"uptime_s\":      %ld,\n"
           "  \"total_ram_mb\":  %lu,\n"
           "  \"free_ram_mb\":   %lu,\n"
           "  \"load_1\":        %.2f,\n"
           "  \"load_5\":        %.2f,\n"
           "  \"load_15\":       %.2f,\n"
           "  \"procs\":         %u,\n"
           "  \"disk_total_gb\": %.2f,\n"
           "  \"disk_free_gb\":  %.2f\n"
           "}\n",
           host,
           uts.sysname, uts.release, uts.machine,
           si.uptime,
           total_ram_mb, free_ram_mb,
           si.loads[0] * load_scale,
           si.loads[1] * load_scale,
           si.loads[2] * load_scale,
           si.procs,
           disk_total, disk_free);

    return 0;
}
