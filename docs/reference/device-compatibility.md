# Device Compatibility Matrix

## Introduction

This reference document provides a comprehensive list of network devices supported by NetRaven, including details about supported features and protocol compatibility by vendor and device model.

## Support Levels

NetRaven offers different levels of device support:

| Support Level | Description |
|--------------|-------------|
| **Full** | All features supported, including backup, restoration, compliance, monitoring, and configuration deployment |
| **Standard** | Core features supported, including backup, restoration, and basic monitoring |
| **Basic** | Essential functionality only, typically limited to backup and basic inventory management |
| **Limited** | Partial support with known limitations |
| **Community** | Support maintained by the community, not officially tested |

## Cisco Devices

### Cisco IOS/IOS XE

| Device Family | Models | Support Level | Backup | Restore | Compliance | Monitoring | Notes |
|--------------|--------|---------------|--------|---------|------------|------------|-------|
| Catalyst Switches | 2960, 3560, 3750, 3850, 9200, 9300, 9400 | Full | ✅ | ✅ | ✅ | ✅ | |
| ISR Routers | 4300, 4400, 1000, 1100, 1900, 2900, 3900 | Full | ✅ | ✅ | ✅ | ✅ | |
| ASR Routers | 1000, 920, 903, 9000 | Full | ✅ | ✅ | ✅ | ✅ | |
| Industrial Switches | IE-3000, IE-4000, IE-5000 | Standard | ✅ | ✅ | ✅ | ⚠️ | Limited performance monitoring |

### Cisco IOS XR

| Device Family | Models | Support Level | Backup | Restore | Compliance | Monitoring | Notes |
|--------------|--------|---------------|--------|---------|------------|------------|-------|
| ASR Routers | 9000, 9900, 9922 | Full | ✅ | ✅ | ✅ | ✅ | |
| NCS Routers | 5500, 5700, 6000 | Full | ✅ | ✅ | ✅ | ✅ | |
| XRv 9000 | Virtual Router | Standard | ✅ | ✅ | ✅ | ⚠️ | Limited performance metrics |

### Cisco NX-OS

| Device Family | Models | Support Level | Backup | Restore | Compliance | Monitoring | Notes |
|--------------|--------|---------------|--------|---------|------------|------------|-------|
| Nexus Switches | 3000, 5000, 7000, 9000 | Full | ✅ | ✅ | ✅ | ✅ | |
| MDS SAN Switches | 9100, 9200, 9300 | Standard | ✅ | ✅ | ✅ | ⚠️ | Limited SAN-specific monitoring |

### Other Cisco Platforms

| Device Family | Models | Support Level | Backup | Restore | Compliance | Monitoring | Notes |
|--------------|--------|---------------|--------|---------|------------|------------|-------|
| ASA Firewalls | 5500, 5500-X, Firepower 1000, 2100 | Full | ✅ | ✅ | ✅ | ✅ | |
| Firepower Threat Defense | FTD on 1000, 2100, 4100, 9300 | Standard | ✅ | ✅ | ✅ | ⚠️ | Limited security metrics |
| Meraki | MX, MS, MR series | Basic | ✅ | ❌ | ⚠️ | ✅ | API-based backup only, no direct restoration |
| SD-WAN (Viptela) | vEdge, cEdge | Standard | ✅ | ✅ | ✅ | ⚠️ | Template-based configuration |

## Juniper Devices

### Juniper Junos OS

| Device Family | Models | Support Level | Backup | Restore | Compliance | Monitoring | Notes |
|--------------|--------|---------------|--------|---------|------------|------------|-------|
| MX Routers | MX5, MX10, MX40, MX80, MX104, MX240, MX480, MX960 | Full | ✅ | ✅ | ✅ | ✅ | |
| EX Switches | EX2300, EX3400, EX4300, EX4600, EX9200 | Full | ✅ | ✅ | ✅ | ✅ | |
| SRX Firewalls | SRX300, SRX550, SRX1500, SRX4100, SRX5800 | Full | ✅ | ✅ | ✅ | ✅ | |
| QFX Switches | QFX5100, QFX5200, QFX10000 | Full | ✅ | ✅ | ✅ | ✅ | |
| ACX Routers | ACX500, ACX1000, ACX2000, ACX4000 | Standard | ✅ | ✅ | ✅ | ⚠️ | Limited performance monitoring |
| PTX Routers | PTX1000, PTX3000, PTX5000, PTX10000 | Standard | ✅ | ✅ | ✅ | ⚠️ | Limited performance monitoring |

## Arista Devices

### Arista EOS

| Device Family | Models | Support Level | Backup | Restore | Compliance | Monitoring | Notes |
|--------------|--------|---------------|--------|---------|------------|------------|-------|
| Fixed Switches | 7010, 7020, 7050, 7060, 7300X3 | Full | ✅ | ✅ | ✅ | ✅ | |
| Modular Switches | 7500R, 7500E, 7800R | Full | ✅ | ✅ | ✅ | ✅ | |
| Virtual Devices | vEOS Router | Standard | ✅ | ✅ | ✅ | ⚠️ | Limited performance metrics |

## HPE/Aruba Devices

### ProVision/ArubaOS-Switch

| Device Family | Models | Support Level | Backup | Restore | Compliance | Monitoring | Notes |
|--------------|--------|---------------|--------|---------|------------|------------|-------|
| 2000 Series | 2530, 2540 | Standard | ✅ | ✅ | ✅ | ⚠️ | |
| 3000 Series | 3810, 3820, 3800 | Standard | ✅ | ✅ | ✅ | ⚠️ | |
| 5000 Series | 5400R, 5400zl | Standard | ✅ | ✅ | ✅ | ⚠️ | |

### ArubaOS (Wireless)

| Device Family | Models | Support Level | Backup | Restore | Compliance | Monitoring | Notes |
|--------------|--------|---------------|--------|---------|------------|------------|-------|
| Mobility Controllers | 7000, 7200, 9000 Series | Basic | ✅ | ✅ | ⚠️ | ⚠️ | Limited compliance checks |
| Instant AP | IAP-3xx, IAP-5xx | Basic | ✅ | ❌ | ❌ | ⚠️ | Backup only via controller |

## F5 Networks

### F5 BIG-IP

| Device Family | Models | Support Level | Backup | Restore | Compliance | Monitoring | Notes |
|--------------|--------|---------------|--------|---------|------------|------------|-------|
| LTM | All hardware platforms, VE | Standard | ✅ | ✅ | ✅ | ⚠️ | Limited application-specific monitoring |
| GTM/DNS | All hardware platforms, VE | Standard | ✅ | ✅ | ✅ | ⚠️ | |
| AFM | All hardware platforms, VE | Basic | ✅ | ✅ | ⚠️ | ⚠️ | Limited security policy compliance |

## Palo Alto Networks

### PAN-OS

| Device Family | Models | Support Level | Backup | Restore | Compliance | Monitoring | Notes |
|--------------|--------|---------------|--------|---------|------------|------------|-------|
| PA Series Firewalls | PA-220, PA-800, PA-3200, PA-5200, PA-7000 | Standard | ✅ | ✅ | ✅ | ⚠️ | Limited security metrics |
| VM-Series | VM-50, VM-100, VM-300, VM-500, VM-700 | Standard | ✅ | ✅ | ✅ | ⚠️ | |
| Panorama | All models, virtual appliance | Basic | ✅ | ✅ | ⚠️ | ⚠️ | Limited management features |

## Check Point

### Check Point GAiA

| Device Family | Models | Support Level | Backup | Restore | Compliance | Monitoring | Notes |
|--------------|--------|---------------|--------|---------|------------|------------|-------|
| Security Gateways | 3000, 5000, 6000, 15000, 23000, 26000 | Basic | ✅ | ⚠️ | ⚠️ | ⚠️ | Partial restore capabilities |
| Security Management | R80.x, R81.x | Basic | ✅ | ⚠️ | ⚠️ | ⚠️ | Backup of management configs only |

## Extreme Networks

### EXOS

| Device Family | Models | Support Level | Backup | Restore | Compliance | Monitoring | Notes |
|--------------|--------|---------------|--------|---------|------------|------------|-------|
| X Series | X440-G2, X460-G2, X670-G2, X870 | Standard | ✅ | ✅ | ✅ | ⚠️ | |
| Summit Series | All models | Standard | ✅ | ✅ | ✅ | ⚠️ | |

## Fortinet

### FortiOS

| Device Family | Models | Support Level | Backup | Restore | Compliance | Monitoring | Notes |
|--------------|--------|---------------|--------|---------|------------|------------|-------|
| FortiGate | 60E-7000 Series, VM | Standard | ✅ | ✅ | ✅ | ⚠️ | Limited security metrics |
| FortiManager | All models, VM | Basic | ✅ | ✅ | ⚠️ | ⚠️ | Management configs only |

## VMware

### NSX

| Device Family | Models | Support Level | Backup | Restore | Compliance | Monitoring | Notes |
|--------------|--------|---------------|--------|---------|------------|------------|-------|
| NSX-T | All versions | Limited | ✅ | ❌ | ⚠️ | ⚠️ | API-based backup only |
| NSX-V | All versions | Limited | ✅ | ❌ | ⚠️ | ⚠️ | Legacy support, API-based backup only |

## Protocol Support Matrix

This table shows which connection protocols are supported for different device operations:

| Vendor | SSH | Telnet | SNMP | API/REST | NETCONF | Notes |
|--------|-----|--------|------|----------|---------|-------|
| Cisco IOS/IOS XE | ✅ | ✅ | ✅ | ⚠️ | ✅ | API support on newer devices only |
| Cisco IOS XR | ✅ | ⚠️ | ✅ | ✅ | ✅ | Telnet disabled by default |
| Cisco NX-OS | ✅ | ⚠️ | ✅ | ✅ | ✅ | Telnet disabled by default |
| Cisco ASA | ✅ | ✅ | ✅ | ⚠️ | ❌ | Limited REST API support |
| Cisco Meraki | ❌ | ❌ | ⚠️ | ✅ | ❌ | Cloud API only |
| Juniper Junos | ✅ | ⚠️ | ✅ | ✅ | ✅ | Preferred NETCONF for config |
| Arista EOS | ✅ | ⚠️ | ✅ | ✅ | ✅ | eAPI recommended |
| HPE/Aruba | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | Limited API support on older models |
| F5 BIG-IP | ✅ | ❌ | ✅ | ✅ | ❌ | iControl REST API recommended |
| Palo Alto Networks | ✅ | ❌ | ✅ | ✅ | ❌ | XML API preferred for config |
| Check Point | ✅ | ❌ | ✅ | ⚠️ | ❌ | Web API for management server |
| Extreme EXOS | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | REST support on newer firmware |
| Fortinet | ✅ | ⚠️ | ✅ | ✅ | ❌ | FortiOS API recommended |
| VMware NSX | ❌ | ❌ | ⚠️ | ✅ | ❌ | REST API only |

## Certification Process

NetRaven conducts rigorous testing on devices before classifying them as fully supported. The certification process includes:

1. **Initial Compatibility Testing**
   - Basic connectivity verification
   - Command syntax validation
   - Configuration parsing verification

2. **Feature Testing**
   - Backup and restore functionality
   - Configuration compliance rules
   - Monitoring capabilities
   - Performance metric collection

3. **Integration Testing**
   - Testing with common network topologies
   - Multi-vendor interoperability scenarios
   - High-availability configurations

4. **Ongoing Compatibility**
   - Regular testing with new firmware releases
   - Validation of new NetRaven features against supported devices
   - Regression testing

## Reporting Compatibility Issues

If you encounter issues with devices listed as supported, or if you're using a device not listed here, please report your experience to help improve our compatibility database:

1. Navigate to **Help** > **Report Device Compatibility Issue**
2. Complete the form with detailed information about:
   - Device make/model
   - Firmware version
   - Feature that failed
   - Error messages received
3. Submit the report for review by our engineering team

## Adding Support for New Devices

NetRaven's device support is continuously expanding. The roadmap for new device support is prioritized based on:

1. Customer requests and requirements
2. Market prevalence of devices
3. Technical feasibility
4. Strategic partner integrations

To request support for a specific device:

1. Navigate to **Help** > **Request Device Support**
2. Provide details about the device
3. Explain your use case and requirements

## Related Documentation

- [Device Management Guide](../user-guide/device-management.md)
- [Configuration Management Guide](../user-guide/configuration-management.md)
- [Connection Protocols Reference](./connection-protocols.md)
- [Custom Device Adapters](../developer-guide/device-adapters.md) 