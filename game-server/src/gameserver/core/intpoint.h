#pragma once

class IntPoint
{
public:
    IntPoint();
    IntPoint(int xpos, int ypos);

    bool isNull() const;

    int x() const;
    int y() const;
    void setX(int x);
    void setY(int y);

    int &rx();
    int &ry();

    IntPoint &operator+=(const IntPoint &p);
    IntPoint &operator-=(const IntPoint &p);
    IntPoint &operator*=(float c);
    IntPoint &operator/=(float c);

    friend inline bool operator==(const IntPoint &, const IntPoint &);
    friend inline bool operator!=(const IntPoint &, const IntPoint &);
    friend inline const IntPoint operator+(const IntPoint &, const IntPoint &);
    friend inline const IntPoint operator-(const IntPoint &, const IntPoint &);
    friend inline const IntPoint operator*(const IntPoint &, float);
    friend inline const IntPoint operator*(float, const IntPoint &);
    friend inline const IntPoint operator-(const IntPoint &);
    friend inline const IntPoint operator/(const IntPoint &, float);

private:
    int xp;
    int yp;
};

/*****************************************************************************
  IntPoint inline functions
 *****************************************************************************/

inline IntPoint::IntPoint()
{
    xp = 0; yp = 0;
}

inline IntPoint::IntPoint(int xpos, int ypos)
{
    xp = xpos; yp = ypos;
}

inline bool IntPoint::isNull() const
{
    return xp == 0 && yp == 0;
}

inline int IntPoint::x() const
{
    return xp;
}

inline int IntPoint::y() const
{
    return yp;
}

inline void IntPoint::setX(int xpos)
{
    xp = xpos;
}

inline void IntPoint::setY(int ypos)
{
    yp = ypos;
}

inline int &IntPoint::rx()
{
    return xp;
}

inline int &IntPoint::ry()
{
    return yp;
}

inline IntPoint &IntPoint::operator+=(const IntPoint &p)
{
    xp += p.xp; yp += p.yp; return *this;
}

inline IntPoint &IntPoint::operator-=(const IntPoint &p)
{
    xp -= p.xp; yp -= p.yp; return *this;
}

inline IntPoint &IntPoint::operator*=(float c)
{
    xp = int(xp*c); yp = int(yp*c); return *this;
}

inline bool operator==(const IntPoint &p1, const IntPoint &p2)
{
    return p1.xp == p2.xp && p1.yp == p2.yp;
}

inline bool operator!=(const IntPoint &p1, const IntPoint &p2)
{
    return p1.xp != p2.xp || p1.yp != p2.yp;
}

inline const IntPoint operator+(const IntPoint &p1, const IntPoint &p2)
{
    return IntPoint(p1.xp + p2.xp, p1.yp + p2.yp);
}

inline const IntPoint operator-(const IntPoint &p1, const IntPoint &p2)
{
    return IntPoint(p1.xp - p2.xp, p1.yp - p2.yp);
}

inline const IntPoint operator*(const IntPoint &p, float c)
{
    return IntPoint(int(p.xp*c), int(p.yp*c));
}

inline const IntPoint operator*(float c, const IntPoint &p)
{
    return IntPoint(int(p.xp*c), int(p.yp*c));
}

inline const IntPoint operator-(const IntPoint &p)
{
    return IntPoint(-p.xp, -p.yp);
}

inline IntPoint &IntPoint::operator/=(float c)
{
    xp = int(xp / c);
    yp = int(yp / c);
    return *this;
}

inline const IntPoint operator/(const IntPoint &p, float c)
{
    return IntPoint(int(p.xp / c), int(p.yp / c));
}

