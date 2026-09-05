# RB-001: DWDM Optical Fiber Cut & Core Transport Degradation
**Category:** Optical Transport Layer
**Triggers:** LOS (Loss of Signal), BGP Neighbor Down on Core Rings, OSPF Route Withdrawal, Downstream Substation Unreachable.

## 1. Initial Assessment
- Confirm OTDR (Optical Time Domain Reflectometer) readings on the affected core interface.
- Determine whether secondary protective optical rings (APS - Automatic Protection Switching) engaged within 50ms.

## 2. Mitigation Steps
- **Step 2.1:** Execute manual BGP traffic reroute via alternate transit path: `set protocols bgp group CORE-TRANSIT neighbor <IP> preference 50`.
- **Step 2.2:** Contact Field Fiber Engineering dispatch with estimated fault distance from OTDR reflection logs.
- **Step 2.3:** Suppress dependent leaf-switch unreachable alerts to reduce NOC noise.