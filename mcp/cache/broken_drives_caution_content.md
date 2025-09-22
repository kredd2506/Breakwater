# NRP Admin Storage: Broken Drives Management - Critical Caution Information

## ⚠️ ADMINISTRATIVE CAUTION
**This page contains administrative documentation intended for cluster administrators and operators. This content may not be relevant for regular users.**

## 🚨 CRITICAL OPERATIONAL PROCEDURES

### Safe OSD Removal Protocol
When removing an Object Storage Daemon (OSD) due to broken drives:

**✅ RECOMMENDED COMMAND:**
```bash
ceph osd crush reweight osd.<id> 0.0
```

**❌ DO NOT USE:**
```bash
ceph osd out osd.<id>
```

**Why this matters:**
- Using `ceph osd out` will immediately shift weight to other OSDs
- This triggers automatic rebalancing which can overwhelm the cluster
- The `crush reweight` method provides controlled, gradual weight reduction
- Allows for safer cluster management during drive failures

## 📊 Monitoring Resources

### Prometheus Integration
- **Direct Link**: [List of Broken Drives in Cluster by Prometheus Monitoring](https://nrp.ai/documentation/admindocs/storage/broken-drives/#list-of-broken-drives-in-the-cluster-by-prometheus-monitoring)
- **Observable Notebook**: [Broken Drives Monitoring Dashboard](https://observablehq.com/d/ad3be6949516bf98)

### Administrative Access Required
This documentation and tools are restricted to:
- Cluster administrators
- Storage infrastructure operators
- Authorized maintenance personnel

## 🔧 Best Practices for Drive Management

1. **Always use controlled weight reduction** with `crush reweight`
2. **Monitor cluster health** before and after any OSD operations
3. **Use Prometheus monitoring** to track drive health proactively
4. **Coordinate with team** before performing drive removal operations
5. **Document all actions** for operational continuity

## ⚠️ Safety Warnings

- Improper OSD removal can cause data loss
- Always verify cluster health before operations
- Use monitoring tools to assess impact
- Follow proper administrative protocols
- Ensure proper backup procedures are in place

---
*This content is extracted from NRP administrative documentation for storage infrastructure management.*