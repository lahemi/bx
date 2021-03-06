from mod_base import *

class Broadcast(Hybrid):
    """Broadcast messages or command output to channels and/or users (targets).

    Usage: broadcast [+-]name target[,target,...] interval command [args]
    Usage: broadcast [+-]name target[,target,...] interval :message
    Usage: broadcast +hello #chan1,#chan2 1h :hello world!
    """
    
    def init(self):
        self.events = [IRC_EVT_INTERVAL]
        self.broadcasts = {}

    def event(self, event):
        for name in self.broadcasts.keys():
            broadcast = self.broadcasts[name]
            if not broadcast["last_exec"]:
                self.RunBroadcast(broadcast)
            elif time.time()-broadcast["last_exec"] > broadcast["interval"]:
                self.RunBroadcast(broadcast)

    def run(self, win, user, data, caller=None):
        args = Args(data)
        hint = "provide [+-]action, targets, interval and command"
        if args.Empty():
            win.Send(hint)
            return False

        name = args[0]
        if name[0] == "-":
            if self.RemoveBroadcast(name[1:]):
                win.Send("broadcast removed")
                return True
            win.Send("no broadcast with that name")
            return False
        elif name[0] == "+":
            name = name[1:]

        if len(args) < 4:
            win.Send(hint)
            return False

        targets = args[1].split(",")
        interval = str_to_seconds(args[2])
        if not interval:
            win.Send("invalid interval")
            return False

        cmd = args[3]
        cmd_args = ""
        if len(args) > 3:
            cmd_args = args.Range(4)

        if cmd[0] != ":":
            command = self.bot.GetCommand(cmd)
            if not command:
                win.Send("cmd does not exists")
                return False

            if command.level > user.GetPermission():
                win.Send("sry, you can't add that command")
                return False

        self.AddBroadcast(name, targets, interval, cmd, cmd_args)
        win.Send("broadcast added")
        return True

    def RunBroadcast(self, broadcast):
        broadcast["last_exec"] = time.time()
        if broadcast["cmd"][0] != ":":
            cmd = self.bot.GetCommand(broadcast["cmd"])
            for target in broadcast["targets"]:
                win = self.bot.GetWindow(target)
                data = broadcast["cmd_args"]
                self.bot.RunCommand(broadcast["cmd"], win, self.bot.me, data)
        else:
            for target in broadcast["targets"]:
                win = self.bot.GetWindow(target)
                msg = broadcast["cmd"][1:]+" "+broadcast["cmd_args"]
                win.Send(msg)

    def AddBroadcast(self, name, targets, interval, cmd, cmd_args):
        broadcast = {
            "targets": targets,
            "interval": interval,
            "cmd": cmd,
            "cmd_args": cmd_args,
            "last_exec": None,
        }
        self.broadcasts[name] = broadcast

    def RemoveBroadcast(self, name):
        if name in self.broadcasts.keys():
            del self.broadcasts[name]
            return True
        return False

module = {
    "class": Broadcast,
    "type": MOD_BOTH,
    "level": 2,
    "zone": IRC_ZONE_BOTH,
    "interval": 1,
    "aliases": ["bc"],
}