import wx
import os
import tempfile
import requests
import pcbnew


class AiRoutingPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.net_filter = wx.TextCtrl(self, value="")
        self.btn_analyze = wx.Button(self, label="Analyze Selected Nets")
        self.log = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)

        vbox.Add(wx.StaticText(self, label="Target nets (comma-separated, optional)"), flag=wx.ALL, border=4)
        vbox.Add(self.net_filter, flag=wx.EXPAND | wx.ALL, border=4)
        vbox.Add(self.btn_analyze, flag=wx.EXPAND | wx.ALL, border=4)
        vbox.Add(wx.StaticText(self, label="Logs"), flag=wx.ALL, border=4)
        vbox.Add(self.log, proportion=1, flag=wx.EXPAND | wx.ALL, border=4)

        self.SetSizer(vbox)

        self.btn_analyze.Bind(wx.EVT_BUTTON, self.on_analyze)

    def export_board_to_dsn(self):
        board = pcbnew.GetBoard()
        tmpdir = tempfile.mkdtemp(prefix="ai-routing-")
        dsn_path = os.path.join(tmpdir, "board.dsn")
        # KiCad 7/8: use the built-in exporter
        exporter = pcbnew.EXPORTER_SPECCTRA(board)
        exporter.SetOutputDirectory(tmpdir)
        exporter.SetFileName("board.dsn")
        exporter.Export()
        return dsn_path, tmpdir

    def on_analyze(self, event):
        try:
            dsn_path, tmpdir = self.export_board_to_dsn()
        except Exception as e:
            self.log.AppendText(f"Export failed: {e}\n")
            return

        nets = self.net_filter.GetValue().strip()
        self.log.AppendText("Sending to backend...\n")
        try:
            with open(dsn_path, "rb") as f:
                resp = requests.post(
                    "http://127.0.0.1:8000/analyze",
                    files={"file": ("board.dsn", f, "application/octet-stream")},
                    data={"target_nets": nets},
                    timeout=120,
                )
            resp.raise_for_status()
            data = resp.json()
            self.log.AppendText(f"Backend response: {data}\n")
        except Exception as e:
            self.log.AppendText(f"Request failed: {e}\n")
        finally:
            # clean up temp
            try:
                import shutil

                shutil.rmtree(tmpdir, ignore_errors=True)
            except Exception:
                pass


class AiRoutingAction(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "AI Routing"
        self.category = "Routing"
        self.description = "AI-assisted routing helper"

    def Run(self):
        frame = wx.GetActiveWindow()
        dlg = wx.Dialog(frame, title="AI Routing", size=(500, 400))
        panel = AiRoutingPanel(dlg)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(panel, 1, wx.EXPAND | wx.ALL, 4)
        dlg.SetSizer(sizer)
        dlg.ShowModal()
        dlg.Destroy()


AiRoutingAction().register()
