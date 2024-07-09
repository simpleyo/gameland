#pragma once

#include "intpoint.h"

class IntRect
{
public:
    IntRect();
    IntRect(int x, int y, int width, int height);

    bool isEmpty() const;

    bool contains(int x, int y) const;
    bool contains(const IntPoint& p) const;

          IntPoint& position()       { return _position; }
    const IntPoint& position() const { return _position; }
          IntPoint& size()           { return _size;     }
    const IntPoint& size()     const { return _size;     }

    friend inline bool operator==(const IntRect &, const IntRect &);
    friend inline bool operator!=(const IntRect &, const IntRect &);

private:
    IntPoint _position;
    IntPoint _size;
};

/*****************************************************************************
  IntRect inline functions
 *****************************************************************************/

inline IntRect::IntRect()
{
}

inline IntRect::IntRect(int x, int y, int width, int height)
{
    _position.rx() = x;
    _position.ry() = y;
    _size.rx() = width;
    _size.ry() = height;
}

inline bool IntRect::isEmpty() const
{
    return _size.x() <= 0 && _size.y() <= 0;
}

inline bool IntRect::contains(int x, int y) const
{
    if ((_size.x() <= 0) || (_size.y() <= 0)) return false;

    if ((x < _position.x()) || 
        (y < _position.y()) ||
        (x >= (_position.x() + _size.x())) ||
        (y >= (_position.y() + _size.y()))) return false;

    return true;
}

inline bool IntRect::contains(const IntPoint& p) const
{
    return contains(p.x(), p.y());
}

inline bool operator==(const IntRect &p1, const IntRect &p2)
{
    return p1.position() == p2.position() && p1.size() == p2.size();
}

inline bool operator!=(const IntRect &p1, const IntRect &p2)
{
    return p1.position() != p2.position() || p1.size() != p2.size();
}

