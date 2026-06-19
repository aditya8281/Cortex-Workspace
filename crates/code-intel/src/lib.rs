//! Cortex Code Intelligence — tree-sitter based AST parsing.

use serde::{Deserialize, Serialize};
use pyo3::prelude::*;

#[derive(Debug, Serialize, Deserialize)]
pub struct CodeNode {
    pub id: u32,
    pub kind: String,
    pub text: String,
    pub start_line: u32,
    pub end_line: u32,
    pub children: Vec<CodeNode>,
}

#[pyfunction]
pub fn parse_python(source: &str) -> PyResult<Vec<CodeNode>> {
    let mut parser = tree_sitter::Parser::new();
    parser.set_language(&tree_sitter_python::LANGUAGE.into())
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to set language: {}", e)))?;
    
    let tree = parser.parse(source, None)
        .ok_or_else(|| pyo3::exceptions::PyRuntimeError::new_err("Failed to parse"))?;
    
    let root = tree.root_node();
    Ok(vec![walk_node(root, source)])
}

fn walk_node(node: tree_sitter::Node, source: &str) -> CodeNode {
    let mut children = Vec::new();
    let mut cursor = node.walk();
    
    for child in node.named_children(&mut cursor) {
        children.push(walk_node(child, source));
    }
    
    CodeNode {
        id: node.id(),
        kind: node.kind().to_string(),
        text: node.utf8_text(source.as_bytes()).unwrap_or("").to_string(),
        start_line: node.start_position().row as u32,
        end_line: node.end_position().row as u32,
        children,
    }
}

#[pymodule]
pub fn cortex_code_intel(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parse_python, m)?)?;
    Ok(())
}
