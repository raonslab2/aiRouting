import wx
import os
import tempfile
import requests
import pcbnew
import base64


class AiRoutingPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.backend_url = wx.TextCtrl(self, value="http://127.0.0.1:8000")
        self.net_filter = wx.TextCtrl(self, value="")
        self.btn_fill_selected = wx.Button(self, label="Use Selected Nets")
        self.btn_analyze = wx.Button(self, label="Analyze")
        self.btn_open_output = wx.Button(self, label="Open Output Folder")
        self.log = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.last_output_dir = None

        vbox.Add(wx.StaticText(self, label="Backend URL"), flag=wx.ALL, border=4)
        vbox.Add(self.backend_url, flag=wx.EXPAND | wx.ALL, border=4)
        vbox.Add(wx.StaticText(self, label="Target nets (comma-separated, optional)"), flag=wx.ALL, border=4)
        vbox.Add(self.net_filter, flag=wx.EXPAND | wx.ALL, border=4)
        vbox.Add(self.btn_fill_selected, flag=wx.EXPAND | wx.ALL, border=4)
        vbox.Add(self.btn_analyze, flag=wx.EXPAND | wx.ALL, border=4)
        vbox.Add(self.btn_open_output, flag=wx.EXPAND | wx.ALL, border=4)
        vbox.Add(wx.StaticText(self, label="Logs"), flag=wx.ALL, border=4)
        vbox.Add(self.log, proportion=1, flag=wx.EXPAND | wx.ALL, border=4)

        self.SetSizer(vbox)

        self.btn_fill_selected.Bind(wx.EVT_BUTTON, self.on_fill_selected)
        self.btn_analyze.Bind(wx.EVT_BUTTON, self.on_analyze)
        self.btn_open_output.Bind(wx.EVT_BUTTON, self.on_open_output)

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

    def on_fill_selected(self, event):
        board = pcbnew.GetBoard()
        nets = set()
        for item in board.GetTracks():
            if item.IsSelected():
                nets.add(item.GetNetname())
        if nets:
            self.net_filter.SetValue(", ".join(sorted(nets)))
        else:
            self.log.AppendText("No selected tracks/vias to infer nets.\n")

    def on_analyze(self, event):
        try:
            dsn_path, tmpdir = self.export_board_to_dsn()
        except Exception as e:
            self.log.AppendText(f"Export failed: {e}\n")
            return

        nets = self.net_filter.GetValue().strip()
        backend = self.backend_url.GetValue().strip() or "http://127.0.0.1:8000"
        self.log.AppendText("Sending to backend...\n")
        try:
            with open(dsn_path, "rb") as f:
                resp = requests.post(
                    f"{backend}/analyze",
                    files={"file": ("board.dsn", f, "application/octet-stream")},
                    data={"target_nets": nets},
                    timeout=120,
                )
            resp.raise_for_status()
            data = resp.json()
            self.log.AppendText(f"Backend response: rc={data.get('return_code')} status={data.get('status')}\n")
            # Save SES/log if returned
            outdir = tempfile.mkdtemp(prefix="ai-routing-out-")
            self.last_output_dir = outdir
            if data.get("ses_b64"):
                ses_path = os.path.join(outdir, data.get("ses_filename", "board.ses"))
                with open(ses_path, "wb") as ses_file:
                    ses_file.write(base64.b64decode(data["ses_b64"]))
                self.log.AppendText(f"Saved SES to {ses_path}\n")
            if data.get("log"):
                log_path = os.path.join(outdir, "freerouting.log")
                with open(log_path, "w", encoding="utf-8") as log_file:
                    log_file.write(data["log"])
                self.log.AppendText(f"Saved log to {log_path}\n")
            if self.last_output_dir:
                self.log.AppendText(f"Output dir: {self.last_output_dir}\n")
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

    def on_open_output(self, event):
        if self.last_output_dir and os.path.isdir(self.last_output_dir):
            try:
                os.startfile(self.last_output_dir)
            except Exception as e:
                self.log.AppendText(f"Cannot open output dir: {e}\n")
        else:
            self.log.AppendText("No output dir available.\n")


AiRoutingAction().register()
