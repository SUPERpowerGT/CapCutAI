use std::time::{SystemTime, UNIX_EPOCH};

use tauri::{
  menu::{MenuBuilder, MenuItemBuilder, PredefinedMenuItem, SubmenuBuilder},
  AppHandle, Runtime, WebviewUrl, WebviewWindowBuilder,
};

fn next_workspace_id() -> String {
  let millis = SystemTime::now()
    .duration_since(UNIX_EPOCH)
    .map(|duration| duration.as_millis())
    .unwrap_or_default();

  format!("workspace_{millis}")
}

fn build_workspace_url(workspace_id: &str) -> WebviewUrl {
  if cfg!(debug_assertions) {
    let url = format!("http://127.0.0.1:3000/?workspaceId={workspace_id}");
    return WebviewUrl::External(url.parse().expect("invalid dev workspace url"));
  }

  WebviewUrl::App(format!("/?workspaceId={workspace_id}").into())
}

fn open_workspace_window<R: Runtime>(app: &AppHandle<R>) -> tauri::Result<()> {
  let workspace_id = next_workspace_id();
  let label = format!("workspace-{}", workspace_id.replace("workspace_", ""));

  WebviewWindowBuilder::new(app, label, build_workspace_url(&workspace_id))
    .title("CapCutAI")
    .inner_size(1560.0, 980.0)
    .min_inner_size(1280.0, 820.0)
    .resizable(true)
    .build()?;

  Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .on_menu_event(|app, event| {
      if event.id().as_ref() == "new_window" {
        let _ = open_workspace_window(app);
      }
    })
    .setup(|app| {
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }

      let new_window = MenuItemBuilder::with_id("new_window", "New Window")
        .accelerator("CmdOrCtrl+Shift+N")
        .build(app)?;
      let close_window = PredefinedMenuItem::close_window(app, Some("Close Window"))?;
      let window_menu = SubmenuBuilder::new(app, "Window")
        .item(&new_window)
        .separator()
        .item(&close_window)
        .build()?;
      let menu = MenuBuilder::new(app).item(&window_menu).build()?;
      app.set_menu(menu)?;

      Ok(())
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
