mod cell_membrane;
use crate::cell_membrane::CellMembrane;
use crate::cell_membrane::CellMembraneParameters;

use pyo3::prelude::*;

#[pyfunction]
fn create() -> PyResult<CellMembrane> {
    let cell_membrane = CellMembrane::default_cell_membrane();
    Ok(cell_membrane)
}

#[pyfunction]
fn voltage(cell_membrane: &CellMembrane) -> PyResult<f64> {
    Ok(cell_membrane.voltage())
}

#[pyfunction]
fn calcium(cell_membrane: &CellMembrane) -> PyResult<f64> {
    Ok(cell_membrane.calcium())
}

#[pyfunction]
fn fired(cell_membrane: &CellMembrane) -> PyResult<bool> {
    Ok(cell_membrane.fired())
}

#[pyfunction]
fn receive_input(cell_membrane: &mut CellMembrane, strength: f64){
    cell_membrane.receive_input(strength);
}

#[pyfunction]
fn update(cell_membrane: &mut CellMembrane){
    let parameters = CellMembraneParameters::default_cell_membrane_parameters();
    cell_membrane.update(&parameters);
}

/// A Python module implemented in Rust. The name of this function must match
/// the `lib.name` setting in the `Cargo.toml`, else Python will not be able to
/// import the module.
#[pymodule]
fn iron_brains(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(create, m)?)?;
    m.add_function(wrap_pyfunction!(voltage, m)?)?;
    m.add_function(wrap_pyfunction!(calcium, m)?)?;
    m.add_function(wrap_pyfunction!(receive_input, m)?)?;
    m.add_function(wrap_pyfunction!(update, m)?)?;
    m.add_function(wrap_pyfunction!(fired, m)?)?;
    //m.add_class::<CellMembrane>()?;
    Ok(())
}


