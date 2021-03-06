#[derive(Copy, Clone, PartialEq)] 
pub enum CellType {
    EXCITE,
    INHIBIT,
}

pub struct CellMembraneParameters {
    voltage_decay: f64,
    current_decay: f64,
    calcium_decay: f64,
    max_voltage: f64,
    voltage_reset: f64,
    calcium_increment: f64,
    input_current_reset: f64,
    reset_input_current: bool,
}

impl CellMembraneParameters{
    pub fn new() -> Self {
	Self {
	    voltage_decay: 0.01,
	    current_decay: 0.03,
	    calcium_decay: 0.1,
	    max_voltage: 1.0,
	    voltage_reset: -1.0,
	    calcium_increment: 1.0,
	    input_current_reset: 0.0,
	    reset_input_current: true,
	}
    }
}

pub struct CellMembrane {
    pub cell_type: CellType,
    voltage: f64, 
    input_current: f64,
    calcium: f64,
    fired: bool,
    pub input_synapse_indexes: std::vec::Vec<usize>,
    pub output_synapse_indexes: std::vec::Vec<usize>,
}

impl CellMembrane {

    // what is the naming convention
    // all kinds of naming issues with file
    pub fn new(cell_type:CellType) -> Self {
	Self {
	    cell_type,
	    voltage: 0.0,
	    input_current: 0.0,
	    calcium: 0.0,
	    fired: false,
	    input_synapse_indexes: std::vec::Vec::new(),
	    output_synapse_indexes: std::vec::Vec::new(),
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

