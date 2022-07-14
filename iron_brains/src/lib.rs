mod model;

use crate::model::Model;

use pyo3::prelude::*;

#[pyfunction]
fn create(size: usize) -> PyResult<Model> {
    let model = Model::new(size);
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
fn update_cells(model: &mut Model){
    model.update_cells();
}

#[pyfunction]
pub fn fired_indexes(model: &mut Model) -> PyResult<std::vec::Vec<usize>> {
    Ok(model.fired_indexes())
}

//////////

#[pyfunction]
fn add_synapse(model: &mut Model, unsupervised_stdp: bool,
	       strength: f64, inhibitory_strength: f64, post_cell_index: i64) -> PyResult<i64>{
    return Ok(model.add_synapse(unsupervised_stdp, strength, inhibitory_strength, post_cell_index));
}

#[pyfunction]
fn positive_normalize(model: &mut Model, cell_index: i64, target: f64) -> PyResult<f64> {
    return Ok(model.positive_normalize(cell_index, target));
}

#[pyfunction]
fn clear_positive_s_tags(model: &mut Model){
    model.clear_positive_s_tags();
}

#[pyfunction]
fn cell_positive_input_strength(model: &Model, cell_index: i64) -> PyResult<f64> {
    Ok(model.cell_positive_input_strength(cell_index))
}

#[pyfunction]
fn s_tag(model: &Model, index: u32) -> PyResult<f64> {
    Ok(model.s_tag(index))
}

#[pyfunction]
fn strength(model: &Model, index: u32) -> PyResult<f64> {
    Ok(model.strength(index))
}

#[pyfunction]
fn inhibitory_strength(model: &Model, index: u32) -> PyResult<f64> {
    Ok(model.inhibitory_strength(index))
}

#[pyfunction]
fn update_s_tag(model: &mut Model, index: u32, s_tag: f64){
    model.update_s_tag(index, s_tag);
}

#[pyfunction]
fn update_strength(model: &mut Model, index: u32, strength: f64){
    model.update_strength(index, strength);
}

#[pyfunction]
fn update_inhibitory_strength(model: &mut Model, index: u32, inhibitory_strength: f64){
    model.update_inhibitory_strength(index, inhibitory_strength);
}

#[pyfunction]
fn update_synapses(model: &mut Model, dopamine: f64){
    model.update_synapses(dopamine);
}

#[pyfunction]
fn cap(model: &mut Model, index: u32){
    model.cap(index);
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
    m.add_function(wrap_pyfunction!(update_cells, m)?)?;
    m.add_function(wrap_pyfunction!(fired_indexes, m)?)?;
    

    m.add_function(wrap_pyfunction!(add_synapse, m)?)?;
    m.add_function(wrap_pyfunction!(clear_positive_s_tags, m)?)?;
    m.add_function(wrap_pyfunction!(positive_normalize, m)?)?;
    m.add_function(wrap_pyfunction!(cell_positive_input_strength, m)?)?;
    m.add_function(wrap_pyfunction!(s_tag, m)?)?;
    m.add_function(wrap_pyfunction!(strength, m)?)?;
    m.add_function(wrap_pyfunction!(inhibitory_strength, m)?)?;
    m.add_function(wrap_pyfunction!(update_s_tag, m)?)?;
    m.add_function(wrap_pyfunction!(update_strength, m)?)?;
    m.add_function(wrap_pyfunction!(update_inhibitory_strength, m)?)?;
    m.add_function(wrap_pyfunction!(update_synapses, m)?)?;
    m.add_function(wrap_pyfunction!(cap, m)?)?;
    
    //m.add_class::<CellMembrane>()?;
    Ok(())
}


