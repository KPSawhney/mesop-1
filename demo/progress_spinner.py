import mesop as me


def load(e: me.LoadEvent):
  me.set_theme_mode("system")


@me.page(
  on_load=load,
  security_policy=me.SecurityPolicy(
    allowed_iframe_parents=["https://google.github.io"]
  ),
  path="/progress_spinner",
)
def app():
  with me.box(style=me.Style(margin=me.Margin.all(15))):
    me.progress_spinner()
