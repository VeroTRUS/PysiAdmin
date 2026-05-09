#!/usr/sbin/dtrace -s
/*
 * PysiAdmin — dtrace/file_monitor.d
 * Traces open(2)/openat(2) on sensitive paths (/etc, /root, /boot).
 */

#pragma D option quiet
#pragma D option switchrate=10hz

syscall::open:entry,
syscall::openat:entry
/stringof(copyinstr(arg0)) != NULL &&
 (strstr(copyinstr(arg0), "/etc/")    != NULL ||
  strstr(copyinstr(arg0), "/root/")   != NULL ||
  strstr(copyinstr(arg0), "/boot/")   != NULL)/
{
    printf("%Y | FILE  | pid=%-6d uid=%-6d comm=%-20s path=%s\n",
           walltimestamp,
           pid, uid, execname,
           copyinstr(arg0));
}
