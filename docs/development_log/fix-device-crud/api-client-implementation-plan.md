# NetRaven API Client Implementation Plan

## Overview

This document outlines a comprehensive plan to implement a typed API client for NetRaven's frontend, leveraging FastAPI's automatic OpenAPI specification generation. This implementation will eliminate URL formatting inconsistencies, improve developer experience, and ensure proper API interactions.

## Goals

1. Validate all API endpoints through automated testing
2. Generate a typed TypeScript client from the OpenAPI specification
3. Create automated tooling for client generation and updates
4. Implement the client in the frontend codebase
5. Document the new approach for developers

## Phase 1: API Validation & Testing (1-2 weeks)

### Tasks

1. **Audit Existing Endpoints**
   - [ ] Review all FastAPI endpoint declarations in the codebase
   - [ ] Ensure all endpoints have proper response models defined
   - [ ] Verify that all path and query parameters are properly typed
   - [ ] Document any inconsistencies or issues found

2. **Enhance API Documentation**
   - [ ] Add detailed docstrings to all endpoint functions
   - [ ] Add descriptions to all schema fields using `Field(..., description="...")`
   - [ ] Add examples to complex schemas using `Field(..., example="...")`
   - [ ] Ensure all endpoint functions have appropriate response status codes

3. **Expand Test Coverage**
   - [ ] Review existing pytest suite for API endpoint coverage
   - [ ] Add tests for any untested endpoints
   - [ ] Create tests that verify response structure matches schema
   - [ ] Add edge case tests for error responses

4. **Validate OpenAPI Specification**
   - [ ] Start the FastAPI server and access `/api/docs` and `/api/openapi.json`
   - [ ] Verify all endpoints are correctly represented
   - [ ] Test endpoints using the Swagger UI to ensure they work as expected
   - [ ] Fix any discrepancies between actual behavior and documentation

### Deliverables

- Complete pytest suite with 90%+ coverage of API endpoints
- Fully documented FastAPI routes with proper type annotations
- Validated OpenAPI specification that accurately represents the API
- Report on any API inconsistencies that need to be addressed

## Phase 2: Client SDK Generation (1 week)

### Tasks

1. **Set Up OpenAPI Generator**
   - [ ] Install OpenAPI Generator CLI in the development environment
   - [ ] Create a configuration file for TypeScript client generation
   - [ ] Determine optimal settings for our specific API structure

2. **Create Generation Scripts**
   - [ ] Create a script to fetch the latest OpenAPI spec from the running API
   - [ ] Create a script to generate the TypeScript client
   - [ ] Add script to package.json: `generate-api-client`
   - [ ] Document the generator settings and process

3. **Automate the Generation Process**
   - [ ] Add client generation step to CI/CD pipeline
   - [ ] Set up hooks to regenerate when API changes (optional)
   - [ ] Create a process for versioning the client

4. **Verify Generated Client**
   - [ ] Generate the client and review the output
   - [ ] Check for any issues or unexpected behaviors
   - [ ] Test basic functionality of the generated client
   - [ ] Document any limitations or special considerations

### Deliverables

- OpenAPI Generator configuration optimized for NetRaven
- Scripts for generating the client SDK
- CI/CD integration for client generation
- Initial version of the generated TypeScript client
- Documentation for the generation process

## Phase 3: Frontend Integration (2-3 weeks)

### Tasks

1. **Create Integration Strategy**
   - [ ] Decide on a gradual implementation approach (by module or feature)
   - [ ] Create patterns for using the client in Pinia stores
   - [ ] Define error handling strategies
   - [ ] Document the transition approach for frontend developers

2. **Implement Client in Core Areas**
   - [ ] Start with the Devices module as a pilot
   - [ ] Refactor API calls to use the generated client
   - [ ] Update error handling to work with the client
   - [ ] Test thoroughly to ensure functionality matches

3. **Expand Implementation**
   - [ ] Gradually refactor other modules to use the client
   - [ ] Update tests to work with the new client
   - [ ] Monitor for any issues or edge cases
   - [ ] Address any limitations encountered

4. **Create Developer Resources**
   - [ ] Document common patterns for using the client
   - [ ] Create examples for different API operations
   - [ ] Update onboarding documentation to include the client
   - [ ] Provide migration guide for existing code

### Deliverables

- Refactored frontend code using the typed API client
- Updated automated tests for frontend components
- Developer documentation for the client usage
- Examples and patterns for common operations

## Phase 4: Evaluation & Optimization (1 week)

### Tasks

1. **Evaluate Implementation**
   - [ ] Review frontend performance with the new client
   - [ ] Gather developer feedback on the new approach
   - [ ] Identify any remaining issues or edge cases
   - [ ] Measure impact on development velocity

2. **Optimize Client Usage**
   - [ ] Look for patterns that could be improved
   - [ ] Create helper functions for common operations
   - [ ] Address any performance concerns
   - [ ] Refine error handling based on real-world usage

3. **Document Lessons Learned**
   - [ ] Document any pitfalls or challenges encountered
   - [ ] Update best practices based on implementation experience
   - [ ] Create a troubleshooting guide for common issues
   - [ ] Share knowledge with the broader team

### Deliverables

- Performance report comparing before and after implementation
- Optimized client usage patterns
- Comprehensive documentation for ongoing maintenance
- Knowledge sharing session for the development team

## Implementation Timeline

| Phase | Description | Duration | Dependencies |
|-------|-------------|----------|--------------|
| 1 | API Validation & Testing | 1-2 weeks | None |
| 2 | Client SDK Generation | 1 week | Phase 1 |
| 3 | Frontend Integration | 2-3 weeks | Phase 2 |
| 4 | Evaluation & Optimization | 1 week | Phase 3 |

Total estimated timeline: 5-7 weeks

## Resource Requirements

- **Backend Developer**: 1 developer for Phase 1, part-time for Phase 2
- **Frontend Developer**: 1 developer for Phase 3, part-time for Phase 2 & 4
- **QA Engineer**: Part-time support throughout for testing
- **DevOps Engineer**: Brief support for CI/CD integration

## Success Criteria

1. All API endpoints are properly documented and tested
2. TypeScript client is successfully generated from the OpenAPI spec
3. Frontend code is refactored to use the typed client
4. URL formatting issues are eliminated
5. Developer feedback is positive regarding the new approach
6. Documentation is comprehensive and clear

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| API specification has errors | Thorough validation in Phase 1 before proceeding |
| Generated client has limitations | Identify early and create workarounds if needed |
| Refactoring introduces bugs | Comprehensive test coverage before and after changes |
| Developer resistance to new approach | Early involvement, clear documentation, and training |
| Timeline extends beyond estimate | Prioritize core features for initial implementation |

## Appendix A: Example Code

### Example Endpoint Documentation

```python
@router.get("/devices/{device_id}", response_model=schemas.device.Device)
def get_device(
    device_id: int,
    db: Session = Depends(get_db_session)
):
    """
    Retrieve a specific network device by ID.
    
    - **device_id**: The unique identifier of the device to retrieve
    
    Returns a complete device object including associated tags.
    
    Raises 404 if the device is not found.
    """
    # Implementation...
```

### Example Schema Documentation

```python
class Device(BaseModel):
    id: int = Field(..., description="Unique identifier for the device")
    hostname: str = Field(..., description="Device hostname", example="core-switch-01")
    ip_address: str = Field(..., description="Device IP address", example="192.168.1.1")
    device_type: str = Field(..., description="Device type (e.g., cisco_ios, juniper_junos)")
    port: int = Field(22, description="SSH port to connect to device")
    description: Optional[str] = Field(None, description="Optional description of the device")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "hostname": "core-switch-01",
                "ip_address": "192.168.1.1",
                "device_type": "cisco_ios",
                "port": 22,
                "description": "Core switch in datacenter 1"
            }
        }
```

### Example Client Generation Script

```bash
#!/bin/bash

# Ensure we're in the project root
cd "$(dirname "$0")/.."

# Make sure the API is running
if ! curl -s http://localhost/api/health > /dev/null; then
    echo "API is not running. Please start it first."
    exit 1
fi

# Fetch the OpenAPI specification
echo "Fetching OpenAPI specification..."
curl -s http://localhost/api/openapi.json > openapi.json

# Check if the spec was fetched successfully
if [ ! -s openapi.json ]; then
    echo "Failed to fetch OpenAPI specification"
    exit 1
fi

# Generate the TypeScript client
echo "Generating TypeScript client..."
npx @openapitools/openapi-generator-cli generate \
    -i openapi.json \
    -g typescript-axios \
    -o ./frontend/src/api-client \
    --additional-properties=supportsES6=true,npmName=netraven-api-client,modelPropertyNaming=camelCase

echo "Client generated successfully in ./frontend/src/api-client"
```

### Example Usage in Frontend

```typescript
// Before
import api from '../services/api';

async function fetchDevices() {
  try {
    const response = await api.get('/api/devices/');
    return response.data;
  } catch (error) {
    console.error("Error fetching devices:", error);
    throw error;
  }
}

// After
import { DevicesApi } from '../api-client';

const devicesApi = new DevicesApi();

async function fetchDevices() {
  try {
    const response = await devicesApi.listDevices();
    return response.data;
  } catch (error) {
    console.error("Error fetching devices:", error);
    throw error;
  }
}
```

## Appendix B: Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAPI Generator Documentation](https://openapi-generator.tech/)
- [TypeScript Axios Client Documentation](https://openapi-generator.tech/docs/generators/typescript-axios)
- [OpenAPI Specification](https://swagger.io/specification/) 