#!/usr/sbin/dtrace -s
/*
 * PysiAdmin — dtrace/priv_monitor.d
 * Alerts on setuid(0) / seteuid(0) privilege escalation attempts.
 */

#pragma D option quiet

syscall::setuid:entry   /arg0 == 0/
{
    printf("%Y | PRIV  | ⚠️  SETUID(0) | pid=%-6d uid=%-6d comm=%s\n",
           walltimestamp, pid, uid, execname);
}

syscall::seteuid:entry  /arg0 == 0/
{
    printf("%Y | PRIV  | ⚠️  SETEUID(0) | pid=%-6d uid=%-6d comm=%s\n",
           walltimestamp, pid, uid, execname);
}

syscall::setreuid:entry /arg0 == 0 || arg1 == 0/
{
    printf("%Y | PRIV  | ⚠️  SETREUID(0) | pid=%-6d uid=%-6d comm=%s\n",
           walltimestamp, pid, uid, execname);
}
