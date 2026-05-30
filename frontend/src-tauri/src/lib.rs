use std::{
  fs,
  path::{Path, PathBuf},
  time::{SystemTime, UNIX_EPOCH},
};

use serde::{Deserialize, Serialize};
use tauri::{
  menu::{MenuBuilder, MenuItemBuilder, PredefinedMenuItem, SubmenuBuilder},
  AppHandle, Manager, Runtime, WebviewUrl, WebviewWindowBuilder,
};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
struct WorkspaceDescriptor {
  workspace_id: String,
  title: String,
  created_at: String,
  last_opened_at: String,
  folder_path: String,
}

#[derive(Debug, Default, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
struct DesktopState {
  last_workspace_id: Option<String>,
}

fn now_stamp() -> String {
  let millis = SystemTime::now()
    .duration_since(UNIX_EPOCH)
    .map(|duration| duration.as_millis())
    .unwrap_or_default();

  millis.to_string()
}

fn next_workspace_id() -> String {
  let millis = now_stamp();
  format!("workspace_{millis}")
}

fn default_workspace_title(workspace_id: &str) -> String {
  let suffix = workspace_id.replace("workspace_", "");
  let short = suffix.chars().take(6).collect::<String>();
  if short.is_empty() {
    "Workspace".to_string()
  } else {
    format!("Workspace {short}")
  }
}

fn app_storage_root<R: Runtime>(app: &AppHandle<R>) -> Result<PathBuf, String> {
  let documents = app
    .path()
    .document_dir()
    .map_err(|error| format!("failed to resolve document dir: {error}"))?;
  Ok(documents.join("CapCutAI"))
}

fn workspace_root_dir<R: Runtime>(app: &AppHandle<R>) -> Result<PathBuf, String> {
  Ok(app_storage_root(app)?.join("Workspaces"))
}

fn desktop_state_path<R: Runtime>(app: &AppHandle<R>) -> Result<PathBuf, String> {
  Ok(app_storage_root(app)?.join("desktop-state.json"))
}

fn workspace_dir(base_dir: &Path, workspace_id: &str) -> PathBuf {
  base_dir.join(workspace_id)
}

fn workspace_manifest_path(base_dir: &Path, workspace_id: &str) -> PathBuf {
  workspace_dir(base_dir, workspace_id).join("workspace.json")
}

fn ensure_dir(path: &Path) -> Result<(), String> {
  fs::create_dir_all(path).map_err(|error| format!("failed to create {}: {error}", path.display()))
}

fn write_json_file<T: Serialize>(path: &Path, value: &T) -> Result<(), String> {
  let serialized =
    serde_json::to_string_pretty(value).map_err(|error| format!("failed to serialize json: {error}"))?;
  fs::write(path, serialized).map_err(|error| format!("failed to write {}: {error}", path.display()))
}

fn read_json_file<T: for<'de> Deserialize<'de>>(path: &Path) -> Result<T, String> {
  let raw = fs::read_to_string(path).map_err(|error| format!("failed to read {}: {error}", path.display()))?;
  serde_json::from_str(&raw).map_err(|error| format!("failed to parse {}: {error}", path.display()))
}

fn load_workspace_descriptor(base_dir: &Path, workspace_id: &str) -> Result<Option<WorkspaceDescriptor>, String> {
  let manifest_path = workspace_manifest_path(base_dir, workspace_id);
  if !manifest_path.exists() {
    return Ok(None);
  }

  read_json_file(&manifest_path).map(Some)
}

fn save_workspace_descriptor(base_dir: &Path, descriptor: &WorkspaceDescriptor) -> Result<(), String> {
  let manifest_path = workspace_manifest_path(base_dir, &descriptor.workspace_id);
  write_json_file(&manifest_path, descriptor)
}

fn touch_workspace_descriptor(
  base_dir: &Path,
  mut descriptor: WorkspaceDescriptor,
) -> Result<WorkspaceDescriptor, String> {
  descriptor.last_opened_at = now_stamp();
  save_workspace_descriptor(base_dir, &descriptor)?;
  Ok(descriptor)
}

fn create_workspace_descriptor(base_dir: &Path) -> Result<WorkspaceDescriptor, String> {
  ensure_dir(base_dir)?;

  let workspace_id = next_workspace_id();
  let workspace_dir = workspace_dir(base_dir, &workspace_id);

  ensure_dir(&workspace_dir)?;
  ensure_dir(&workspace_dir.join("assets").join("reference"))?;
  ensure_dir(&workspace_dir.join("assets").join("source"))?;
  ensure_dir(&workspace_dir.join("assets").join("images"))?;
  ensure_dir(&workspace_dir.join("assets").join("audio"))?;
  ensure_dir(&workspace_dir.join("artifacts").join("materials"))?;
  ensure_dir(&workspace_dir.join("artifacts").join("plans"))?;
  ensure_dir(&workspace_dir.join("artifacts").join("renders"))?;
  ensure_dir(&workspace_dir.join("cache"))?;
  ensure_dir(&workspace_dir.join("logs"))?;

  let now = now_stamp();
  let descriptor = WorkspaceDescriptor {
    workspace_id: workspace_id.clone(),
    title: default_workspace_title(&workspace_id),
    created_at: now.clone(),
    last_opened_at: now,
    folder_path: workspace_dir.display().to_string(),
  };

  save_workspace_descriptor(base_dir, &descriptor)?;
  Ok(descriptor)
}

fn read_desktop_state<R: Runtime>(app: &AppHandle<R>) -> Result<DesktopState, String> {
  let path = desktop_state_path(app)?;
  if !path.exists() {
    return Ok(DesktopState::default());
  }

  read_json_file(&path)
}

fn write_desktop_state<R: Runtime>(app: &AppHandle<R>, state: &DesktopState) -> Result<(), String> {
  let path = desktop_state_path(app)?;
  if let Some(parent) = path.parent() {
    ensure_dir(parent)?;
  }

  write_json_file(&path, state)
}

fn persist_last_workspace<R: Runtime>(app: &AppHandle<R>, workspace_id: &str) -> Result<(), String> {
  write_desktop_state(
    app,
    &DesktopState {
      last_workspace_id: Some(workspace_id.to_string()),
    },
  )
}

fn resolve_workspace_descriptor<R: Runtime>(
  app: &AppHandle<R>,
  explicit_workspace_id: Option<String>,
) -> Result<WorkspaceDescriptor, String> {
  let base_dir = workspace_root_dir(app)?;
  ensure_dir(&base_dir)?;

  let descriptor = if let Some(workspace_id) = explicit_workspace_id {
    match load_workspace_descriptor(&base_dir, &workspace_id)? {
      Some(existing) => touch_workspace_descriptor(&base_dir, existing)?,
      None => {
        let created = create_workspace_descriptor(&base_dir)?;
        if created.workspace_id == workspace_id {
          created
        } else {
          // Create the explicitly requested folder shape if the URL carried an id we do not know yet.
          let requested_dir = workspace_dir(&base_dir, &workspace_id);
          ensure_dir(&requested_dir)?;
          ensure_dir(&requested_dir.join("assets").join("reference"))?;
          ensure_dir(&requested_dir.join("assets").join("source"))?;
          ensure_dir(&requested_dir.join("assets").join("images"))?;
          ensure_dir(&requested_dir.join("assets").join("audio"))?;
          ensure_dir(&requested_dir.join("artifacts").join("materials"))?;
          ensure_dir(&requested_dir.join("artifacts").join("plans"))?;
          ensure_dir(&requested_dir.join("artifacts").join("renders"))?;
          ensure_dir(&requested_dir.join("cache"))?;
          ensure_dir(&requested_dir.join("logs"))?;
          let now = now_stamp();
          let descriptor = WorkspaceDescriptor {
            workspace_id: workspace_id.clone(),
            title: default_workspace_title(&workspace_id),
            created_at: now.clone(),
            last_opened_at: now,
            folder_path: requested_dir.display().to_string(),
          };
          save_workspace_descriptor(&base_dir, &descriptor)?;
          descriptor
        }
      }
    }
  } else {
    let state = read_desktop_state(app)?;
    if let Some(last_workspace_id) = state.last_workspace_id {
      match load_workspace_descriptor(&base_dir, &last_workspace_id)? {
        Some(existing) => touch_workspace_descriptor(&base_dir, existing)?,
        None => create_workspace_descriptor(&base_dir)?,
      }
    } else {
      create_workspace_descriptor(&base_dir)?
    }
  };

  persist_last_workspace(app, &descriptor.workspace_id)?;
  Ok(descriptor)
}

fn build_workspace_url(workspace_id: &str) -> WebviewUrl {
  if cfg!(debug_assertions) {
    let url = format!("http://127.0.0.1:3001/?workspaceId={workspace_id}");
    return WebviewUrl::External(url.parse().expect("invalid dev workspace url"));
  }

  WebviewUrl::App(format!("/?workspaceId={workspace_id}").into())
}

fn open_workspace_window_with_descriptor<R: Runtime>(
  app: &AppHandle<R>,
  descriptor: &WorkspaceDescriptor,
) -> Result<(), String> {
  let label = format!(
    "workspace-{}",
    descriptor.workspace_id.replace("workspace_", "")
  );

  log::info!("opening workspace window: {}", descriptor.workspace_id);

  WebviewWindowBuilder::new(app, label, build_workspace_url(&descriptor.workspace_id))
    .title("CapCutAI")
    .inner_size(1560.0, 980.0)
    .min_inner_size(1280.0, 820.0)
    .resizable(true)
    .build()
    .map_err(|error| format!("failed to build workspace window: {error}"))?;

  Ok(())
}

fn open_new_workspace_window<R: Runtime>(app: &AppHandle<R>) -> Result<(), String> {
  let base_dir = workspace_root_dir(app)?;
  let descriptor = create_workspace_descriptor(&base_dir)?;
  persist_last_workspace(app, &descriptor.workspace_id)?;
  open_workspace_window_with_descriptor(app, &descriptor)
}

fn build_app_menu<R: Runtime>(app: &AppHandle<R>) -> tauri::Result<tauri::menu::Menu<R>> {
  let new_window = MenuItemBuilder::with_id("new_window", "New Window")
    .accelerator("CmdOrCtrl+Shift+N")
    .build(app)?;
  let close_window = PredefinedMenuItem::close_window(app, Some("Close Window"))?;
  let minimize = PredefinedMenuItem::minimize(app, Some("Minimize"))?;
  let maximize = PredefinedMenuItem::maximize(app, Some("Zoom"))?;
  let fullscreen = PredefinedMenuItem::fullscreen(app, Some("Toggle Full Screen"))?;
  let quit = PredefinedMenuItem::quit(app, Some("Quit CapCutAI"))?;
  let undo = PredefinedMenuItem::undo(app, Some("Undo"))?;
  let redo = PredefinedMenuItem::redo(app, Some("Redo"))?;
  let cut = PredefinedMenuItem::cut(app, Some("Cut"))?;
  let copy = PredefinedMenuItem::copy(app, Some("Copy"))?;
  let paste = PredefinedMenuItem::paste(app, Some("Paste"))?;
  let select_all = PredefinedMenuItem::select_all(app, Some("Select All"))?;

  let file_menu = SubmenuBuilder::new(app, "File")
    .item(&new_window)
    .separator()
    .item(&close_window)
    .separator()
    .item(&quit)
    .build()?;
  let edit_menu = SubmenuBuilder::new(app, "Edit")
    .item(&undo)
    .item(&redo)
    .separator()
    .item(&cut)
    .item(&copy)
    .item(&paste)
    .separator()
    .item(&select_all)
    .build()?;
  let view_menu = SubmenuBuilder::new(app, "View")
    .item(&fullscreen)
    .build()?;
  let window_menu = SubmenuBuilder::new(app, "Window")
    .item(&new_window)
    .separator()
    .item(&minimize)
    .item(&maximize)
    .separator()
    .item(&close_window)
    .build()?;
  let help_menu = SubmenuBuilder::new(app, "Help").build()?;

  MenuBuilder::new(app)
    .item(&file_menu)
    .item(&edit_menu)
    .item(&view_menu)
    .item(&window_menu)
    .item(&help_menu)
    .build()
}

#[tauri::command]
fn ensure_workspace<R: Runtime>(
  app: AppHandle<R>,
  workspace_id: Option<String>,
) -> Result<WorkspaceDescriptor, String> {
  resolve_workspace_descriptor(&app, workspace_id)
}

#[tauri::command]
fn create_workspace<R: Runtime>(app: AppHandle<R>) -> Result<WorkspaceDescriptor, String> {
  let base_dir = workspace_root_dir(&app)?;
  let descriptor = create_workspace_descriptor(&base_dir)?;
  persist_last_workspace(&app, &descriptor.workspace_id)?;
  Ok(descriptor)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .invoke_handler(tauri::generate_handler![ensure_workspace, create_workspace])
    .on_menu_event(|app, event| {
      if event.id().as_ref() == "new_window" {
        if let Err(error) = open_new_workspace_window(app) {
          log::error!("failed to open workspace window: {error}");
        }
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

      let menu = build_app_menu(app.handle())?;
      app.set_menu(menu)?;

      Ok(())
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
