#[derive(Copy, Clone, PartialEq)] 
pub enum CellType {
    EXCITE,
    INHIBIT,
}

use pyo3::prelude::*;

#[derive(Copy, Clone, PartialEq)] 
#[pyclass]
pub struct CellMembraneParameters {
    voltage_decay: f64,
    current_decay: f64,
    calcium_decay: f64,
    pub starting_membrane_voltage: f64,
    max_voltage: f64,
    voltage_reset: f64,
    calcium_increment: f64,
    input_current_reset: f64,
    pub starting_calcium: f64,
    pub starting_input_current: f64,
    reset_input_current: bool,
}

#[pymethods]
impl CellMembraneParameters{
    #[new]
    pub fn new(voltage_decay: f64, current_decay: f64, calcium_decay: f64,
	       starting_membrane_voltage: f64,
	       max_voltage: f64, voltage_reset: f64,
	       calcium_increment: f64, input_current_reset: f64,
	       starting_calcium: f64,
	       starting_input_current: f64,
	       reset_input_current: bool) -> Self {
	Self {
	    voltage_decay,
	    current_decay,
	    calcium_decay,
	    starting_membrane_voltage,
	    max_voltage,
	    voltage_reset,
	    calcium_increment,
	    input_current_reset,
	    starting_calcium,
	    starting_input_current,
	    reset_input_current,
	}
    }
}


pub struct CellMembrane {
    pub cell_type: CellType,
    voltage: f64, 
    input_current: f64,
    calcium: f64,
    fired: bool,
}

impl CellMembrane {

    // what is the naming convention
    // all kinds of naming issues with file
    pub fn new(cell_type:CellType, voltage: f64, input_current: f64, calcium: f64) -> Self {
	Self {
	    cell_type,
	    voltage,
	    input_current,
	    calcium,
	    fired: false,
	}
    }

    pub fn update(&mut self, parameters: &CellMembraneParameters) {
        self.fired = false;
        if self.voltage > parameters.max_voltage {
            self.voltage = parameters.voltage_reset;
            self.fired = true;
            self.calcium += parameters.calcium_increment;
            if parameters.reset_input_current {
		self.input_current = parameters.input_current_reset;
	    }
	}

	let voltage_factor: f64 = 1.0 - parameters.voltage_decay;
        self.voltage = self.voltage * voltage_factor;
        self.voltage += self.input_current;
	let input_current_factor:f64 = 1.0 - parameters.current_decay;
        self.input_current = self.input_current * input_current_factor;
        self.calcium = self.calcium * (1.0 - parameters.calcium_decay);
    }

    pub fn voltage(&self) -> f64 {
	self.voltage
    }

    pub fn fired(&self) -> bool {
	self.fired
    }

    pub fn calcium(&self) -> f64 {
	self.calcium
    }

    pub fn receive_input(&mut self, strength: f64) {
	self.input_current = self.input_current + strength
    }
}

