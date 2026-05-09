#!/usr/sbin/dtrace -s
/*
 * PysiAdmin — dtrace/exec_monitor.d
 * Traces execve(2) on FreeBSD, OpenBSD, NetBSD.
 * Run: sudo dtrace -s dtrace/exec_monitor.d
 */

#pragma D option quiet
#pragma D option switchrate=10hz

syscall::execve:entry
{
    printf("%Y | EXEC  | pid=%-6d ppid=%-6d uid=%-6d comm=%-20s file=%s\n",
           walltimestamp,
           pid, ppid, uid,
           execname,
           copyinstr(arg0));
}
