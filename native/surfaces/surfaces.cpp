#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <vector>
struct Error {int32_t code;char message[252];};
struct V {double x,y,z;};
V add(V a,V b){return {a.x+b.x,a.y+b.y,a.z+b.z};}
V sub(V a,V b){return {a.x-b.x,a.y-b.y,a.z-b.z};}
V scale(V a,double b){return {a.x*b,a.y*b,a.z*b};}
double plane(V a){return a.x*.22+a.y+a.z*.13;}
struct Descriptor {
    double cell_x,cell_z,seed,foot_x,foot_z,rx,rz,lx,lz,height,radius,individual,spread;
};
static_assert(sizeof(Descriptor)==13*sizeof(double),"Packed source descriptor");
extern "C" __declspec(dllexport) int32_t __cdecl zw_surface_abi(uint32_t* abi,uint32_t* bits){if(!abi||!bits)return 1;*abi=1;*bits=sizeof(void*)*8;return 0;}
extern "C" __declspec(dllexport) int32_t __cdecl zw_specimens(const Descriptor* input,uint32_t count,float* output,uint64_t capacity,uint64_t* written,Error* error){
    try {
        if(!input || !output || !written || !count || count>24 || capacity<count*192ull)throw std::invalid_argument("Invalid bounded crystal batch/output");
        for(uint32_t i=0;i<count;i++) {
            const auto* values=reinterpret_cast<const double*>(&input[i]);
            for(int j=0;j<13;j++)if(!std::isfinite(values[j]))throw std::invalid_argument("Nonfinite crystal descriptor");
            const auto& d=input[i];
            if(d.seed<.27 || d.seed>1 || d.height<=0 || d.height>100 || d.radius<=0 || d.radius>100 || d.individual<=.18 || d.individual>1)throw std::invalid_argument("Invalid crystal dimensions/recipe");
        }
        uint64_t vertex=0;
        for(uint32_t index=0;index<count;index++) {
            const auto& d=input[index];const double pi=3.141592653589793238462643383279502884;
            const int sides=d.seed>.66?4:6;
            const double cap=d.seed>.66 ? .10+.18*d.individual : .32+.42*d.individual;
            const double broken=d.individual>.62 ? .12+.24*std::fmod(d.individual*7.1,1.) : .015;
            const double rad=d.radius/std::cos(pi/sides);
            const double cx=(d.cell_x+.5)*2.8+d.rx*d.spread+d.foot_x,cz=(d.cell_z+.5)*2.8+d.rz*d.spread+d.foot_z;
            const double dx=d.rx*d.rz-d.rz*d.rx,dz=-d.rz*d.rz-d.rx*d.rx;
            auto polygon=[&](const std::vector<V>& points,V normal){
                if(points.size()<3)return;
                const double nx=d.rx*normal.x+d.rz*normal.z,nz=-d.rz*normal.x+d.rx*normal.z;
                const double ny=normal.y+(d.lx*normal.x+d.lz*normal.z);
                for(size_t i=1;i+1<points.size();i++)for(size_t j:std::array<size_t,3>{0,i,i+1}) {
                    if(vertex>=capacity)throw std::runtime_error("Crystal output bound exceeded");
                    const auto q=points[j];const double x=q.x-d.lx*q.y,z=q.z-d.lz*q.y;
                    float* dst=output+vertex++*12;
                    const double values[12]={d.rx*x+d.rz*z+cx,q.y-2.5,-d.rz*x+d.rx*z+cz,nx,ny,nz,dx,dz,q.y,d.seed,1.+d.seed,1.};
                    for(int k=0;k<12;k++)dst[k]=static_cast<float>(values[k]);
                }
            };
            std::vector<V> base,shoulder;std::vector<double> angles;
            for(int i=0;i<sides;i++) {
                const double a=i*(pi*2)/sides+(sides==4?pi/4:0);angles.push_back(a);
                base.push_back({rad*std::cos(a),0,rad*std::sin(a)});shoulder.push_back(add(base.back(),{0,d.height-cap,0}));
            }
            const V tip{0,d.height,0};std::vector<V> cuts;
            auto face=[&](const std::vector<V>& points,V n){
                std::vector<V> clipped;
                for(size_t i=0;i<points.size();i++) {
                    auto a=points[i],b=points[(i+1)%points.size()];double fa=plane(a)-(d.height-broken),fb=plane(b)-(d.height-broken);
                    if(fa<=0)clipped.push_back(a);
                    if((fa<=0)!=(fb<=0)){auto q=add(a,scale(sub(b,a),fa/(fa-fb)));clipped.push_back(q);cuts.push_back(q);}
                }
                polygon(clipped,n);
            };
            face(base,{0,-1,0});
            for(int i=0;i<sides;i++) {
                int j=(i+1)%sides;double a=angles[i]+pi/sides;V n{std::cos(a),0,std::sin(a)};
                face({base[i],base[j],shoulder[j],shoulder[i]},n);
                face({shoulder[i],shoulder[j],tip},add(n,{0,d.radius/cap,0}));
            }
            if(!cuts.empty()) {
                std::vector<std::array<double,3>> keys;std::vector<V> unique;
                for(auto q:cuts) {
                    std::array<double,3> key{std::nearbyint(q.x*1e8)/1e8,std::nearbyint(q.y*1e8)/1e8,std::nearbyint(q.z*1e8)/1e8};
                    auto p=std::find(keys.begin(),keys.end(),key);
                    if(p==keys.end()){keys.push_back(key);unique.push_back(q);}else unique[static_cast<size_t>(p-keys.begin())]=q;
                }
                V c{0,0,0};for(auto q:unique)c=add(c,q);c=scale(c,1./unique.size());
                std::stable_sort(unique.begin(),unique.end(),[&](V a,V b){return std::atan2(a.z-c.z,a.x-c.x)<std::atan2(b.z-c.z,b.x-c.x);});
                polygon(unique,{.22,1,.13});
            }
        }
        *written=vertex;if(error){error->code=0;error->message[0]=0;}return 0;
    }catch(const std::exception& e){if(error){error->code=1;strncpy_s(error->message,e.what(),_TRUNCATE);}return 1;}
    catch(...){if(error){error->code=2;strcpy_s(error->message,"Native crystal allocation failed; reference remains available");}return 2;}
}
