#pragma once

#include "types.h"

template <typename T, T invalid_value>
struct TIDR
{
private:
    static const T INVALID = invalid_value;
public:
    TIDR() : value(INVALID) {}
    TIDR(const T& v) : value(v) {}
    operator T() const { return value; }
    explicit operator bool() const { return is_valid(); }
    TIDR& operator=(const T& other) { value = other; return *this; }
    bool is_valid() const { return value != INVALID; }
    void invalidate() { value = INVALID; }
private:
    T    value;
};

using IDR64 = TIDR<uint64, 0xFFFFFFFFFFFFFFFF>;
using IDR   = TIDR<uint,   0xFFFFFFFF>;
using IDR16 = TIDR<ushort, 0xFFFF>;
using IDR8  = TIDR<ubyte,  0xFF>;

struct RoomSlotId {
    void invalidate() { room_id.invalidate(); slot_id.invalidate(); }
    bool is_valid() const { return room_id.is_valid() && slot_id.is_valid(); }

    IDR room_id;
    IDR slot_id;
};