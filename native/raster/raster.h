#pragma once
#include <stdint.h>
#define ZW_API extern "C" __declspec(dllexport) int32_t __cdecl
// ABI 1: process-local context/version handles; RGBA8 premultiplied sRGB,
// bottom-up rows. No pointer or handle is a cross-process identity.
struct ZwError { int32_t code; char message[252]; };
struct ZwRegion { uint32_t x,y,width,height; uint64_t stride,length; void* data; };
struct ZwTile { uint64_t id; uint32_t x,y,width,height; uint64_t length; const void* data; };
struct ZwStats { uint64_t bytes,peak_bytes,versions,tiles,copied_bytes,read_bytes; };
ZW_API zw_abi(uint32_t*,uint32_t*,uint32_t*);
ZW_API zw_open(uint64_t limit,void** context,ZwError*);
ZW_API zw_close(void*,ZwError*);
ZW_API zw_limit(void*,uint64_t,ZwError*);
ZW_API zw_create(void*,uint32_t,uint32_t,const void*,uint64_t,uint64_t,uint64_t*,ZwError*);
ZW_API zw_import(void*,uint32_t,uint32_t,const ZwTile*,uint32_t,uint64_t*,ZwError*);
ZW_API zw_patch(void*,uint64_t,const ZwRegion*,uint32_t,uint64_t*,ZwError*);
ZW_API zw_retain(void*,uint64_t,ZwError*);
ZW_API zw_release(void*,uint64_t,ZwError*);
ZW_API zw_read(void*,uint64_t,const ZwRegion*,uint32_t,ZwError*);
ZW_API zw_tiles(void*,uint64_t,ZwTile*,uint32_t,uint32_t*,ZwError*);
ZW_API zw_stats(void*,ZwStats*,ZwError*);
ZW_API zw_add(const void*,const void*,void*,uint64_t,ZwError*);
// Optional ABI-1 extension: tightly packed four-byte pixels/coverage, exact
// reference float32 constraint evaluation; no context/handle ownership.
ZW_API zw_constrain(const void*,const void*,const void*,void*,uint64_t,double,ZwError*);

// Optional ABI-1 Fill extension: packed byte predicates/results, four-neighbor
// connected component, bounded scratch, interlocked cancellation; no handles.
ZW_API zw_connected(const void*,uint64_t,uint32_t,uint32_t,uint32_t,uint32_t,void*,uint64_t,volatile int32_t*,double,ZwError*);

ZW_API zw_cancel(volatile int32_t*,int32_t,ZwError*);
