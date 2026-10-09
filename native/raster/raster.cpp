#include "raster.h"
#include <algorithm>
#include <atomic>
#include <cstring>
#include <memory>
#include <mutex>
#include <stdexcept>
#include <unordered_map>
#include <vector>
#include <limits>
#include <cmath>
#include <emmintrin.h>
#include <intrin.h>
#include <chrono>
namespace {
constexpr uint32_t side=128;
struct LimitError:std::runtime_error {using std::runtime_error::runtime_error;};
struct Budget { std::atomic<uint64_t> bytes{0},peak{0},tiles{0},copied{0},read{0}; uint64_t limit; };
struct Tile {
    std::shared_ptr<Budget> budget; uint64_t id; uint32_t w,h; std::vector<uint8_t> pixels;
    Tile(std::shared_ptr<Budget> b,uint64_t i,uint32_t width,uint32_t height):budget(b),id(i),w(width),h(height) {
        const uint64_t n=uint64_t(w)*h*4;
        if(n>budget->limit || budget->bytes>budget->limit-n)throw LimitError("Native unique-tile budget exhausted; prior versions retained");
        pixels.resize(size_t(n));budget->bytes+=n;budget->tiles++;
        auto p=budget->peak.load();while(p<budget->bytes && !budget->peak.compare_exchange_weak(p,budget->bytes.load())){}
    }
    ~Tile(){budget->bytes-=pixels.size();budget->tiles--;}
};
struct Version { uint32_t w,h; std::vector<std::shared_ptr<Tile>> tiles; uint64_t refs=1; };
struct Core {std::mutex mutex;std::shared_ptr<Budget> budget=std::make_shared<Budget>();std::unordered_map<uint64_t,Version> versions;std::unordered_map<uint64_t,std::weak_ptr<Tile>> imports;uint64_t next=1,tile_id=1;};
Core& core(void* p){if(!p)throw std::invalid_argument("Missing native context");return *static_cast<Core*>(p);}
Version& version(Core& c,uint64_t id){auto p=c.versions.find(id);if(p==c.versions.end())throw std::invalid_argument("Expired native version");return p->second;}
uint64_t insert(Core& c,Version&& v){if(c.versions.size()>=256)throw LimitError("256 native versions retained; release unused leases");auto id=c.next++;c.versions.emplace(id,std::move(v));return id;}
void dimensions(uint32_t w,uint32_t h){if(!w||!h||w>8192||h>8192||uint64_t(w)*h>8388608)throw std::invalid_argument("Native raster dimensions exceed limits");}
void region(const Version& v,const ZwRegion& r){if(!r.width||!r.height||r.x>v.w||r.y>v.h||r.width>v.w-r.x||r.height>v.h-r.y||!r.data||r.stride<uint64_t(r.width)*4||(r.height>1 && r.stride>(std::numeric_limits<uint64_t>::max()-uint64_t(r.width)*4)/(r.height-1))||r.length<r.stride*(r.height-1)+uint64_t(r.width)*4)throw std::invalid_argument("Invalid native region/buffer/stride");}
template<class F> int32_t protect(ZwError* error,F f){try{f();if(error){error->code=0;error->message[0]=0;}return 0;}catch(const LimitError& ex){if(error){error->code=2;strncpy_s(error->message,ex.what(),_TRUNCATE);}return 2;}catch(const std::bad_alloc&){if(error){error->code=2;strcpy_s(error->message,"Native allocation failed; prior versions retained");}return 2;}catch(const std::exception& ex){if(error){error->code=1;strncpy_s(error->message,ex.what(),_TRUNCATE);}return 1;}catch(...){if(error){error->code=3;strcpy_s(error->message,"Unknown native failure; prior versions retained");}return 3;}}
}
ZW_API zw_abi(uint32_t* abi,uint32_t* tile,uint32_t* bits){if(!abi||!tile||!bits)return 1;*abi=1;*tile=side;*bits=sizeof(void*)*8;return 0;}
ZW_API zw_open(uint64_t limit,void** out,ZwError* e){return protect(e,[&]{if(!out||!limit)throw std::invalid_argument("Invalid native opening limit");auto c=std::make_unique<Core>();c->budget->limit=limit;*out=c.release();});}
ZW_API zw_close(void* p,ZwError* e){return protect(e,[&]{auto& c=core(p);{std::lock_guard<std::mutex> l(c.mutex);if(!c.versions.empty())throw std::runtime_error("Native readers/versions still retained");}delete &c;});}
ZW_API zw_limit(void* p,uint64_t limit,ZwError* e){return protect(e,[&]{auto& c=core(p);std::lock_guard<std::mutex> l(c.mutex);c.budget->limit=limit;});}
ZW_API zw_create(void* p,uint32_t w,uint32_t h,const void* data,uint64_t length,uint64_t stride,uint64_t* out,ZwError* e){return protect(e,[&]{dimensions(w,h);if(!out||!data||stride<uint64_t(w)*4||(h>1 && stride>(std::numeric_limits<uint64_t>::max()-uint64_t(w)*4)/(h-1))||length<stride*(h-1)+uint64_t(w)*4)throw std::invalid_argument("Invalid initial native buffer");auto& c=core(p);std::lock_guard<std::mutex> l(c.mutex);Version v{w,h};for(uint32_t y=0;y<h;y+=side)for(uint32_t x=0;x<w;x+=side){auto t=std::make_shared<Tile>(c.budget,c.tile_id++,std::min(side,w-x),std::min(side,h-y));for(uint32_t iy=0;iy<t->h;iy++)memcpy(t->pixels.data()+uint64_t(iy)*t->w*4,static_cast<const uint8_t*>(data)+uint64_t(y+iy)*stride+x*4,t->w*4);c.budget->copied+=t->pixels.size();v.tiles.push_back(t);}*out=insert(c,std::move(v));});}
ZW_API zw_import(void* p,uint32_t w,uint32_t h,const ZwTile* input,uint32_t count,uint64_t* out,ZwError* e){return protect(e,[&]{dimensions(w,h);if(!out||!input||count!=((w+side-1)/side)*((h+side-1)/side))throw std::invalid_argument("Invalid transferable tile table");auto& c=core(p);std::lock_guard<std::mutex> l(c.mutex);for(auto at=c.imports.begin();at!=c.imports.end();){if(at->second.expired())at=c.imports.erase(at);else ++at;}Version v{w,h};uint32_t i=0;for(uint32_t y=0;y<h;y+=side)for(uint32_t x=0;x<w;x+=side){const auto& a=input[i++];if(!a.id||a.x!=x||a.y!=y||a.width!=std::min(side,w-x)||a.height!=std::min(side,h-y)||a.length!=uint64_t(a.width)*a.height*4||!a.data)throw std::invalid_argument("Invalid immutable transfer tile");auto t=c.imports[a.id].lock();if(t && (t->w!=a.width||t->h!=a.height))throw std::invalid_argument("Transfer identity dimensions changed");if(!t){t=std::make_shared<Tile>(c.budget,c.tile_id++,a.width,a.height);memcpy(t->pixels.data(),a.data,size_t(a.length));c.budget->copied+=a.length;c.imports[a.id]=t;}v.tiles.push_back(t);}*out=insert(c,std::move(v));for(auto at=c.imports.begin();at!=c.imports.end();){if(at->second.expired())at=c.imports.erase(at);else ++at;}});}
ZW_API zw_patch(void* p,uint64_t base,const ZwRegion* patches,uint32_t count,uint64_t* out,ZwError* e){return protect(e,[&]{if(!out||!patches||!count||count>2048)throw std::invalid_argument("Invalid native patch batch");auto& c=core(p);std::lock_guard<std::mutex> l(c.mutex);Version v=version(c,base);v.refs=1;for(uint32_t i=0;i<count;i++)region(v,patches[i]);std::unordered_map<size_t,std::shared_ptr<Tile>> changed;const uint32_t columns=(v.w+side-1)/side;for(uint32_t i=0;i<count;i++){const auto& r=patches[i];for(uint32_t ty=r.y/side;ty<=(r.y+r.height-1)/side;ty++)for(uint32_t tx=r.x/side;tx<=(r.x+r.width-1)/side;tx++){const size_t index=size_t(ty)*columns+tx;auto& t=changed[index];if(!t){auto old=v.tiles[index];t=std::make_shared<Tile>(c.budget,c.tile_id++,old->w,old->h);t->pixels=old->pixels;c.budget->copied+=t->pixels.size();v.tiles[index]=t;}const auto x=std::max(r.x,tx*side),y=std::max(r.y,ty*side),endx=std::min(r.x+r.width,tx*side+t->w),endy=std::min(r.y+r.height,ty*side+t->h);for(uint32_t iy=y;iy<endy;iy++)memcpy(t->pixels.data()+(uint64_t(iy-ty*side)*t->w+x-tx*side)*4,static_cast<const uint8_t*>(r.data)+uint64_t(iy-r.y)*r.stride+(x-r.x)*4,(endx-x)*4);}}*out=insert(c,std::move(v));});}
ZW_API zw_retain(void* p,uint64_t id,ZwError* e){return protect(e,[&]{auto& c=core(p);std::lock_guard<std::mutex> l(c.mutex);version(c,id).refs++;});}
ZW_API zw_release(void* p,uint64_t id,ZwError* e){return protect(e,[&]{auto& c=core(p);std::lock_guard<std::mutex> l(c.mutex);if(!--version(c,id).refs)c.versions.erase(id);});}
ZW_API zw_read(void* p,uint64_t id,const ZwRegion* regions,uint32_t count,ZwError* e){return protect(e,[&]{if(!regions||!count||count>2048)throw std::invalid_argument("Invalid native read batch");auto& c=core(p);Version v;{std::lock_guard<std::mutex> l(c.mutex);v=version(c,id);}for(uint32_t i=0;i<count;i++)region(v,regions[i]);const uint32_t columns=(v.w+side-1)/side;for(uint32_t i=0;i<count;i++){const auto& r=regions[i];for(uint32_t y=r.y;y<r.y+r.height;y++){uint32_t x=r.x;while(x<r.x+r.width){auto t=v.tiles[size_t(y/side)*columns+x/side];uint32_t n=std::min(r.x+r.width-x,t->w-x%side);memcpy(static_cast<uint8_t*>(r.data)+uint64_t(y-r.y)*r.stride+(x-r.x)*4,t->pixels.data()+(uint64_t(y%side)*t->w+x%side)*4,n*4);x+=n;}}c.budget->read+=uint64_t(r.width)*r.height*4;}});}
ZW_API zw_tiles(void* p,uint64_t id,ZwTile* out,uint32_t capacity,uint32_t* count,ZwError* e){return protect(e,[&]{if(!count)throw std::invalid_argument("Missing tile count");auto& c=core(p);std::lock_guard<std::mutex> l(c.mutex);auto& v=version(c,id);*count=uint32_t(v.tiles.size());if(!out)return;if(capacity<v.tiles.size())throw std::invalid_argument("Tile table capacity too small");const uint32_t columns=(v.w+side-1)/side;for(size_t i=0;i<v.tiles.size();i++){auto t=v.tiles[i];out[i]={t->id,uint32_t(i%columns)*side,uint32_t(i/columns)*side,t->w,t->h,t->pixels.size(),t->pixels.data()};}});}
ZW_API zw_stats(void* p,ZwStats* out,ZwError* e){return protect(e,[&]{if(!out)throw std::invalid_argument("Missing statistics buffer");auto& c=core(p);std::lock_guard<std::mutex> l(c.mutex);auto b=c.budget;*out={b->bytes,b->peak,uint64_t(c.versions.size()),b->tiles,b->copied,b->read};});}
ZW_API zw_add(const void* back,const void* source,void* target,uint64_t length,ZwError* e){return protect(e,[&]{if(!back||!source||!target||length%4||length>128*1024*1024)throw std::invalid_argument("Invalid Add region buffers");auto b=static_cast<const uint8_t*>(back),s=static_cast<const uint8_t*>(source);auto d=static_cast<uint8_t*>(target);for(uint64_t i=0;i<length;i+=4){uint32_t ab=b[i+3],a=s[i+3];for(uint32_t k=0;k<3;k++){uint32_t first=a*b[i+k],second=ab*(a-s[i+k]),excess=std::max(first,second)-second+127;d[i+k]=uint8_t(b[i+k]+s[i+k]-((excess+1+(excess>>8))>>8));}uint32_t alpha=ab*(255-a)+127;d[i+3]=uint8_t(a+((alpha+1+(alpha>>8))>>8));}});}
ZW_API zw_constrain(const void* before,const void* after,const void* coverage,void* target,uint64_t length,double opacity,ZwError* e){return protect(e,[&]{
    if(!before||!after||!coverage||!target||!length||length%4||length>128*1024*1024||!std::isfinite(opacity)||opacity<0.||opacity>1.)throw std::invalid_argument("Invalid constraint region buffers/opacity");
    auto a=static_cast<const uint8_t*>(before),b=static_cast<const uint8_t*>(after),mask=static_cast<const uint8_t*>(coverage);auto d=static_cast<uint8_t*>(target);
    // Match NumPy's separate float32 multiplies/add and nearest-even rint.
    // /fp:strict prevents contraction or reordered arithmetic. Restore the
    // thread's rounding mode on return; no callbacks/allocations in this loop.
    const auto previous=_mm_getcsr();_mm_setcsr((previous&~_MM_ROUND_MASK)|_MM_ROUND_NEAREST);
    const float scale=static_cast<float>(opacity/255.);const auto zero=_mm_setzero_si128();const auto one=_mm_set1_ps(1.f);
    for(uint64_t i=0;i<length;i+=4){
        uint32_t pa,pb;memcpy(&pa,a+i,4);memcpy(&pb,b+i,4);
        auto va=_mm_cvtepi32_ps(_mm_unpacklo_epi16(_mm_unpacklo_epi8(_mm_cvtsi32_si128(pa),zero),zero));
        auto vb=_mm_cvtepi32_ps(_mm_unpacklo_epi16(_mm_unpacklo_epi8(_mm_cvtsi32_si128(pb),zero),zero));
        auto factor=_mm_set1_ps(static_cast<float>(mask[i+3])*scale);
        auto value=_mm_add_ps(_mm_mul_ps(va,_mm_sub_ps(one,factor)),_mm_mul_ps(vb,factor));
        auto integers=_mm_cvtps_epi32(value);auto packed=_mm_packus_epi16(_mm_packs_epi32(integers,zero),zero);const uint32_t pixel=_mm_cvtsi128_si32(packed);memcpy(d+i,&pixel,4);
    }
    _mm_setcsr(previous);
});}

ZW_API zw_connected(const void* input,uint64_t input_length,uint32_t w,uint32_t h,uint32_t x,uint32_t y,void* result,uint64_t result_length,volatile int32_t* cancelled,double seconds,ZwError* e){return protect(e,[&]{
    dimensions(w,h);const auto n=uint64_t(w)*h;
    if(!input||!result||input_length!=n||result_length!=n||x>=w||y>=h||!cancelled||!std::isfinite(seconds)||seconds<=0.||seconds>30.)throw std::invalid_argument("Invalid connected Fill buffers/seed/budget");
    auto matches=static_cast<const uint8_t*>(input);auto output=static_cast<uint8_t*>(result);
    const auto began=std::chrono::steady_clock::now();
    auto checkpoint=[&]{
        if(_InterlockedCompareExchange(reinterpret_cast<volatile long*>(cancelled),0,0))throw std::invalid_argument("Obsolete Fill cancelled; artwork unchanged");
        if(std::chrono::duration<double>(std::chrono::steady_clock::now()-began).count()>seconds)throw std::invalid_argument("Fill exceeded its 30 s computation budget; artwork unchanged");
    };
    checkpoint();memset(output,0,size_t(n));const uint32_t seed=y*w+x;if(!matches[seed])return;
    // Each pixel is scheduled once. At most n int32 entries (32 MiB at 8 MP),
    // plus the caller's n-byte output; no callback or Python per-pixel work.
    std::vector<uint32_t> todo(static_cast<size_t>(n));size_t count=1;todo[0]=seed;output[seed]=1;uint32_t visits=0;
    auto push=[&](uint32_t at){if(matches[at]&&!output[at]){output[at]=1;todo[count++]=at;}};
    while(count){
        const auto at=todo[--count];const auto px=at%w;
        if(px)push(at-1);
        if(px+1<w)push(at+1);
        if(at>=w)push(at-w);
        if(uint64_t(at)+w<n)push(at+w);
        if((++visits&4095)==0)checkpoint();
    }
    checkpoint();
});}

ZW_API zw_cancel(volatile int32_t* flag,int32_t value,ZwError* e){return protect(e,[&]{if(!flag)throw std::invalid_argument("Missing cancellation flag");_InterlockedExchange(reinterpret_cast<volatile long*>(flag),value);});}
