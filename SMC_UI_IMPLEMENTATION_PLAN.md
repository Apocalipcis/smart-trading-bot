# SMC Strategy Configuration System UI Implementation Plan

## **Current State Analysis:**
1. ✅ **Backend**: Complete SMC strategy configuration system with 4 presets (conservative, aggressive, scalping, custom)
2. ✅ **Backend**: SMC strategy API endpoints for validation and parameters
3. ✅ **UI**: Basic backtesting form with timeframe roles and basic parameters
4. ❌ **UI**: No access to SMC configuration presets
5. ❌ **UI**: No SMC-specific parameter configuration
6. ❌ **UI**: No preset selection and customization

## **Implementation Plan:**

### **Phase 1: Add SMC Configuration Presets API**
1. **Create new API endpoint** `/api/v1/strategies/smc/presets` to serve SMC configuration presets
2. **Add preset management endpoints** for CRUD operations on SMC presets
3. **Extend strategy validation** to include SMC-specific configuration validation

### **Phase 2: Enhance UI Types and API Client**
1. **Add SMC configuration types** to `web/src/types/api.ts`:
   - `SMCConfiguration` interface
   - `SMCPreset` interface
   - `SMCIndicators` interface
   - `SMCFilters` interface
   - `SMCElements` interface
   - `SMCRiskManagement` interface

2. **Extend API client** in `web/src/services/api.ts`:
   - `getSMCPresets()` method
   - `getSMCPreset(name: string)` method
   - `validateSMCConfiguration(config: SMCConfiguration)` method

### **Phase 3: Create SMC Configuration Component**
1. **Create new component** `web/src/components/SMCConfiguration.tsx`:
   - Preset selection dropdown
   - Configuration parameter forms for each section
   - Real-time validation
   - Preset customization options

2. **Integrate with Backtests component** to replace basic strategy parameters

### **Phase 4: Enhanced Backtesting Form**
1. **Update Backtests.tsx** to include:
   - SMC preset selection
   - Advanced SMC parameter configuration
   - Configuration validation and warnings
   - Preset save/load functionality

### **Phase 5: Configuration Management**
1. **Add preset management UI**:
   - Save custom configurations
   - Import/export configurations
   - Preset comparison view
   - Configuration templates

## **Technical Implementation Details:**

### **New API Endpoints:**
```python
# GET /api/v1/strategies/smc/presets
# GET /api/v1/strategies/smc/presets/{preset_name}
# POST /api/v1/strategies/smc/presets
# PUT /api/v1/strategies/smc/presets/{preset_name}
# DELETE /api/v1/strategies/smc/presets/{preset_name}
# POST /api/v1/strategies/smc/validate
```

### **UI Components Structure:**
```
SMCConfiguration/
├── PresetSelector.tsx
├── IndicatorsConfig.tsx
├── FiltersConfig.tsx
├── SMCElementsConfig.tsx
├── RiskManagementConfig.tsx
└── ConfigurationValidator.tsx
```

### **Data Flow:**
1. User selects SMC strategy in backtest form
2. UI loads available SMC presets
3. User selects preset or customizes parameters
4. Configuration is validated before backtest creation
5. Backtest runs with SMC configuration
6. Results include SMC-specific metrics and analysis

## **Benefits:**
1. **Professional SMC Trading**: Access to proven SMC configuration presets
2. **Customization**: Full control over SMC parameters and filters
3. **Validation**: Real-time configuration validation
4. **Preset Management**: Save and share custom configurations
5. **Better Results**: Optimized SMC strategy performance

## **Files to Modify/Create:**
- **Backend**: `src/api/routers/strategies.py` (add SMC preset endpoints)
- **Frontend**: `web/src/types/api.ts` (add SMC types)
- **Frontend**: `web/src/services/api.ts` (add SMC API methods)
- **Frontend**: `web/src/components/SMCConfiguration.tsx` (new component)
- **Frontend**: `web/src/components/Backtests.tsx` (integrate SMC config)

## **Implementation Order:**
1. Backend API endpoints for SMC presets
2. Frontend types and API client methods
3. SMC Configuration component
4. Integration with Backtests component
5. Testing and validation
