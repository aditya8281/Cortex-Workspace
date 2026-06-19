//! Cortex File Watcher — watches filesystem changes and emits events.

use notify::{Watcher, RecursiveMode, Result, event::{Event, EventKind}};
use std::sync::mpsc::channel;
use std::path::Path;

fn main() -> Result<()> {
    let (tx, rx) = channel();
    
    let mut watcher = notify::recommended_watcher(tx)?;
    watcher.watch(Path::new("."), RecursiveMode::Recursive)?;
    
    println!("File watcher started. Watching for changes...");
    
    for res in rx {
        match res {
            Ok(event) => handle_event(event),
            Err(e) => eprintln!("Watch error: {}", e),
        }
    }
    
    Ok(())
}

fn handle_event(event: Event) {
    match event.kind {
        EventKind::Create(_) => println!("Created: {:?}", event.paths),
        EventKind::Modify(_) => println!("Modified: {:?}", event.paths),
        EventKind::Remove(_) => println!("Removed: {:?}", event.paths),
        _ => {}
    }
}
