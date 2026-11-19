"""Build the console: app/template.html + out/app_data.json + app/geo.json + app/logo.b64 -> index.html (and app/nova_sentinel_app.html)."""
import os
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H)
t = open(os.path.join(H, "template.html"), encoding="utf-8").read()
t = (t.replace("__DATA__", open(os.path.join(R, "out", "app_data.json"), encoding="utf-8").read())
      .replace("__GEO__", open(os.path.join(H, "geo.json"), encoding="utf-8").read())
      .replace("__LOGO__", open(os.path.join(H, "logo.b64"), encoding="utf-8").read().strip()))
for out in (os.path.join(R, "index.html"), os.path.join(H, "nova_sentinel_app.html")):
    open(out, "w", encoding="utf-8").write(t)
print("built", len(t), "bytes")
