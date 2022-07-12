mod model;

use crate::model::Model;
use crate::model::cell_membrane::CellMembraneParameters;

use pyo3::prelude::*;

#[pyfunction]
fn create(size: u32) -> PyResult<Model> {
    let model = Model::default_model(size);
    Ok(model)
}

#[pyfunction]
fn voltage(model: &Model, index: u32) -> PyResult<f64> {
    Ok(model.voltage(index))
}

#[pyfunction]
fn calcium(model: &Model, index: u32) -> PyResult<f64> {
    Ok(model.calcium(index))
}

#[pyfunction]
fn fired(model: &Model, index: u32) -> PyResult<bool> {
    Ok(model.fired(index))
}

#[pyfunction]
fn receive_input(model: &mut Model, index: u32, strength: f64){
    model.receive_input(index, strength);
}

#[pyfunction]
fn update(model: &mut Model){
    let parameters = CellMembraneParameters::default_cell_membrane_parameters();
    model.update(&parameters);
}

/// A Python module implemented in Rust. The name of this function must match
/// the `lib.name` setting in the `Cargo.toml`, else Python will not be able to
/// import the module.
#[pymodule]
fn iron_brains(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(create, m)?)?;
    m.add_function(wrap_pyfunction!(voltage, m)?)?;
    m.add_function(wrap_pyfunction!(calcium, m)?)?;
    m.add_function(wrap_pyfunction!(fired, m)?)?;
    m.add_function(wrap_pyfunction!(receive_input, m)?)?;
    m.add_function(wrap_pyfunction!(update, m)?)?;
    //m.add_class::<CellMembrane>()?;
    Ok(())
}


