// Stateless ABI 1, x64: bottom-up premultiplied RGBA -> top-down Qt BGRA.
// Caller pins source/destination for this one batched call. No retained pointers,
// decoder/Qt/GL objects, allocations, jobs, global state or audio ownership.
#include <cstdint>
#include <cstring>
#include <limits>
#include <emmintrin.h>
extern "C" __declspec(dllexport) int zw_media_abi(std::uint32_t* abi, std::uint32_t* bits) noexcept {
    if (!abi || !bits) return 1;
    *abi=1; *bits=sizeof(void*)*8; return 0;
}
extern "C" __declspec(dllexport) int zw_media_qt(const void* source, std::uint64_t source_bytes,
    void* destination, std::uint64_t destination_bytes, std::uint32_t width, std::uint32_t height,
    std::uint64_t destination_stride) noexcept {
    const std::uint64_t pixels=std::uint64_t(width)*height, row=std::uint64_t(width)*4;
    if (!source || !destination || !width || !height || pixels>8388608 || source_bytes!=pixels*4 ||
        destination_stride<row || destination_stride>std::numeric_limits<std::uint64_t>::max()/height ||
        destination_bytes<destination_stride*height) return 1;
    const auto* input=static_cast<const std::uint8_t*>(source);
    auto* output=static_cast<std::uint8_t*>(destination);
    const auto ga=_mm_set1_epi32(static_cast<int>(0xff00ff00u));
    const auto red=_mm_set1_epi32(0x000000ff);
    const auto blue=_mm_set1_epi32(0x00ff0000);
    for(std::uint32_t y=0; y<height; ++y) {
        const auto* src=input+std::uint64_t(height-y-1)*row;
        auto* dst=output+std::uint64_t(y)*destination_stride;
        std::uint32_t x=0;
        for(; x+4<=width; x+=4) {
            const auto v=_mm_loadu_si128(reinterpret_cast<const __m128i*>(src+std::uint64_t(x)*4));
            const auto converted=_mm_or_si128(_mm_and_si128(v,ga),_mm_or_si128(_mm_slli_epi32(_mm_and_si128(v,red),16),_mm_srli_epi32(_mm_and_si128(v,blue),16)));
            _mm_storeu_si128(reinterpret_cast<__m128i*>(dst+std::uint64_t(x)*4),converted);
        }
        for(; x<width; ++x) {
            std::uint32_t v; std::memcpy(&v,src+std::uint64_t(x)*4,4);
            v=(v&0xff00ff00u)|((v&0x000000ffu)<<16)|((v&0x00ff0000u)>>16);
            std::memcpy(dst+std::uint64_t(x)*4,&v,4);
        }
    }
    return 0;
}
