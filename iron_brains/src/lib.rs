mod model;
use crate::model::Model;
use model::cell_membrane::CellType;
use model::cell_membrane::CellMembraneParameters;
use model::synapse::SynapseParameters;
use model::synapse::LayerSynapseParameters;

use pyo3::prelude::*;

#[pyfunction]
fn create(size: usize,
	  cell_membrane_parameters: CellMembraneParameters,
	  synapse_parameters: SynapseParameters) -> PyResult<Model> {
    let model = Model::new(size, cell_membrane_parameters, synapse_parameters);
    Ok(model)
}

#[pyfunction]
fn add_cell(model: &mut Model, cell_type: usize) -> PyResult<usize>{
    return if cell_type == 0 {
	Ok(model.add_cell(CellType::EXCITE))
    } else {
	Ok(model.add_cell(CellType::INHIBIT))
    };
}

#[pyfunction]
fn apply_fire(model: &mut Model, index: usize) {
    model.apply_fire(index);
}

#[pyfunction]
fn voltage(model: &Model, index: usize) -> PyResult<f64> {
    Ok(model.voltage(index))
}

#[pyfunction]
fn receive_input(model: &mut Model, index: usize, strength: f64){
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
fn add_synapse(model: &mut Model,
	       layer_parameters: LayerSynapseParameters,
	       strength: f64, inhibitory_strength: f64,
	       pre_cell_index: usize,
	       post_cell_index: usize) -> PyResult<usize>{
    return Ok(model.add_synapse(layer_parameters,
				strength, inhibitory_strength,
				pre_cell_index, post_cell_index));
}

#[pyfunction]
fn positive_normalize(model: &mut Model, cell_index: usize, target: f64) -> PyResult<f64> {
    return Ok(model.positive_normalize(cell_index, target));
}

#[pyfunction]
fn clear_positive_s_tags(model: &mut Model){
    model.clear_positive_s_tags();
}

#[pyfunction]
fn cell_positive_input_strength(model: &Model, cell_index: usize) -> PyResult<f64> {
    Ok(model.cell_positive_input_strength(cell_index))
}

#[pyfunction]
fn strength(model: &Model, index: usize) -> PyResult<f64> {
    Ok(model.strength(index))
}

#[pyfunction]
fn inhibitory_strength(model: &Model, index: usize) -> PyResult<f64> {
    Ok(model.inhibitory_strength(index))
}

#[pyfunction]
fn update_strength(model: &mut Model, index: usize, strength: f64){
    model.update_strength(index, strength);
}

#[pyfunction]
fn update_inhibitory_strength(model: &mut Model, index: usize, inhibitory_strength: f64){
    model.update_inhibitory_strength(index, inhibitory_strength);
}

#[pyfunction]
fn update_synapses(model: &mut Model, dopamine: f64){
    model.update_synapses(dopamine);
}

#[pyfunction]
fn cap(model: &mut Model, index: usize){
    model.cap(index);
}

/// A Python module implemented in Rust. The name of this function must match
/// the `lib.name` setting in the `Cargo.toml`, else Python will not be able to
/// import the module.
#[pymodule]
fn iron_brains(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(create, m)?)?;
    m.add_function(wrap_pyfunction!(add_cell, m)?)?;
    m.add_function(wrap_pyfunction!(apply_fire, m)?)?;
    m.add_function(wrap_pyfunction!(voltage, m)?)?;

    m.add_function(wrap_pyfunction!(receive_input, m)?)?;
    m.add_function(wrap_pyfunction!(update_cells, m)?)?;
    m.add_function(wrap_pyfunction!(fired_indexes, m)?)?;
    
    m.add_function(wrap_pyfunction!(add_synapse, m)?)?;
    m.add_function(wrap_pyfunction!(clear_positive_s_tags, m)?)?;
    m.add_function(wrap_pyfunction!(positive_normalize, m)?)?;
    m.add_function(wrap_pyfunction!(cell_positive_input_strength, m)?)?;
    
    m.add_function(wrap_pyfunction!(strength, m)?)?;
    m.add_function(wrap_pyfunction!(inhibitory_strength, m)?)?;
    m.add_function(wrap_pyfunction!(update_strength, m)?)?;
    m.add_function(wrap_pyfunction!(update_inhibitory_strength, m)?)?;
    m.add_function(wrap_pyfunction!(update_synapses, m)?)?;
    m.add_function(wrap_pyfunction!(cap, m)?)?;
    
    m.add_class::<CellMembraneParameters>()?;
    m.add_class::<SynapseParameters>()?;
    m.add_class::<LayerSynapseParameters>()?;
    Ok(())
}


