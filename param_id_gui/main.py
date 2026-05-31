"""Application entry point for param_id_gui."""

import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the application."""
    try:
        from PySide6.QtWidgets import QApplication
        from param_id_gui.gui.main_window import MainWindow
        from param_id_gui.core.orchestrator import Orchestrator
        from param_id_gui.core.data_bus import DataBus
        from param_id_gui.core.model_registry import ModelRegistry
        from param_id_gui.core.simulation_controller import SimulationController
        
        # Try to import C++ compatibility layer
        try:
            from param_id_gui.core._core_compat import get_core
            core = get_core()
            if core:
                logger.info("C++ core module loaded successfully")
            else:
                logger.warning("C++ core not available, using Python fallback")
        except Exception as e:
            logger.warning("C++ core loading failed: %s", e)
        
        # Create core components
        orchestrator = Orchestrator()
        data_bus = DataBus()
        model_registry = ModelRegistry()
        
        # Create simulation controller
        controller = SimulationController(orchestrator, data_bus, model_registry)
        
        # Register default models
        _register_default_models(model_registry)
        
        # Create application
        app = QApplication(sys.argv)
        
        # Create and show main window
        window = MainWindow()
        window.set_controller(controller)
        window.show()
        
        logger.info("Application started")
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"Error: {e}")
        print("Please install PySide6: pip install PySide6")
        sys.exit(1)
    except Exception as e:
        logger.exception("Application error")
        print(f"Fatal error: {e}")
        sys.exit(1)


def _register_default_models(registry: 'ModelRegistry') -> None:
    """Register default models in the registry.
    
    Args:
        registry: ModelRegistry instance
    """
    from param_id_gui.models.motor.pmsm_dq import PMSMdqModel
    from param_id_gui.models.power.power_models import BuckConverter, BoostConverter
    from param_id_gui.core.model_registry import ModelMetadata
    from param_id_gui.core.types import ModelType, FidelityLevel
    
    # Register PMSM model
    try:
        pmsm = PMSMdqModel()
        pmsm_meta = ModelMetadata(
            model_id="PMSM",
            model_name="PMSM dq-axis Model",
            domain=ModelType.MOTOR,
            fidelity=FidelityLevel.L2_LUMPED,
            version="1.0.0",
            sim_step_ns=50000  # 50μs
        )
        registry.register(pmsm, pmsm_meta)
        logger.info("Registered PMSM model")
    except Exception as e:
        logger.warning("Failed to register PMSM model: %s", e)
    
    # Register Buck converter model
    try:
        buck = BuckConverter()
        buck_meta = ModelMetadata(
            model_id="Buck Converter",
            model_name="Buck Converter Model",
            domain=ModelType.POWER,
            fidelity=FidelityLevel.L2_LUMPED,
            version="1.0.0",
            sim_step_ns=10000  # 10μs
        )
        registry.register(buck, buck_meta)
        logger.info("Registered Buck Converter model")
    except Exception as e:
        logger.warning("Failed to register Buck Converter model: %s", e)
    
    # Register Boost converter model
    try:
        boost = BoostConverter()
        boost_meta = ModelMetadata(
            model_id="Boost Converter",
            model_name="Boost Converter Model",
            domain=ModelType.POWER,
            fidelity=FidelityLevel.L2_LUMPED,
            version="1.0.0",
            sim_step_ns=10000  # 10μs
        )
        registry.register(boost, boost_meta)
        logger.info("Registered Boost Converter model")
    except Exception as e:
        logger.warning("Failed to register Boost Converter model: %s", e)


if __name__ == "__main__":
    main()
