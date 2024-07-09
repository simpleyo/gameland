#pragma once

#include <iostream>
#include <cstdlib>

#include "error_macros.h"
#include "types.h"
#include "core/math/math_2d.h"
#include "core/intpoint.h"
#include "idr.h"
#include "core/logger.h"
#include "trace.h"
#include "handshake.h"

#ifdef RTCHECK   // Runtime check   
    #error RTCHECK already defined
#else
    namespace app { void fatal_error(); }

    //#define RTCHECK(x) {if (!(x)) { ::std::cout << "Condition failed:" << #x << "\n" << __FILE__ << " ---> " << __LINE__; ::std::cin.get(); ::exit(1);}}
    #define RTCHECK(x) {if (!(x)) { std::ostringstream out; out << "Condition failed:" << #x << "\n" << __FILE__ << " ---> " << __LINE__ << std::endl; logger_log(out.str()); app::fatal_error(); ::std::cin.get(); ::exit(1);}}

    //#define RTCHECK(x) ERR_FAIL_COND(!(x))
    //#define RTCHECK_V(x,v) ERR_FAIL_COND_V(!(x),v)
#endif

#define STRINGIFY(x) #x

// Template explicit specialization
#define DECLARE_SET_FLAGS(T)                                                          \
template <bool b>                                                                     \
void _set_flags(T& value, uint flags);                                                \
template <> inline void _set_flags<true> (T& value, uint flags) { value |= flags;  }  \
template <> inline void _set_flags<false>(T& value, uint flags) { value &= ~flags; }

DECLARE_SET_FLAGS(unsigned char)
DECLARE_SET_FLAGS(ushort)
DECLARE_SET_FLAGS(uint)

#undef DECLARE_SET_FLAGS

template<typename T> void safe_delete(T*& x) 
{
    RTCHECK(x != NULL); 
    delete x; 
    x = NULL;
}

#define GET_SINGLETON(t, n) auto* n = t::get_singleton(); RTCHECK(n);
#define SINGLETON(t) t::get_singleton()





