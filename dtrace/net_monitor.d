#!/usr/sbin/dtrace -s
/*
 * PysiAdmin — dtrace/net_monitor.d
 * Traces connect(2) on BSD systems.
 */

#pragma D option quiet
#pragma D option switchrate=10hz

syscall::connect:entry
{
    printf("%Y | NET   | pid=%-6d uid=%-6d comm=%-20s fd=%d\n",
           walltimestamp,
           pid, uid, execname, arg0);
}
