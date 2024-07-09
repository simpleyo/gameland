#pragma once

#include <array>

#include "circularbufferbase.h"

template <typename T, uint N>
class CircularArray : public CircularBufferBase<std::array<T, N>>
{
    using Base = CircularBufferBase<std::array<T, N>>;

public:
    CircularArray() : Base() {}

};
