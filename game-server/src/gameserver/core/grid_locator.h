#pragma once

#include "types.h"
#include "math/math_2d.h"

class GridLocator 
{
public:
    GridLocator() {}

    void initialize(uint cell_coord_bits, uint cell_size_bits);
    
    uint get_intersecting_cells(const Rect2& r, IDR* cell_ids, uint max_cell_ids) const;
    uint get_intersecting_cells(float ax, float ay, float bx, float by, IDR* cell_ids, uint max_cell_ids) const;

    Point2i get_cell_coords(IDR cell_id) const;

    IDR get_cell_id(const Point2i& cell_coords) const;

private:
    uint _cell_coord_bits;
    uint _cell_size_bits;
    uint _world_coord_bits;
    uint _max_world_coords;
    uint _max_cell_coords;
    uint _last_cell_coord;
};

inline
void GridLocator::initialize(uint cell_coord_bits, uint cell_size_bits)
{
    _cell_coord_bits = cell_coord_bits;
    _cell_size_bits = cell_size_bits;
    RTCHECK(cell_coord_bits > 0);
    RTCHECK(cell_coord_bits <= 16);
    RTCHECK(_cell_size_bits > 0);
    _world_coord_bits = _cell_coord_bits + _cell_size_bits;
    _max_world_coords = (1 << _world_coord_bits);
    _max_cell_coords = (1 << cell_coord_bits);
    _last_cell_coord = (1 << cell_coord_bits) - 1;
}

inline
IDR GridLocator::get_cell_id(const Point2i& cell_coords) const
{
    const uint x = cell_coords.x & _last_cell_coord;
    const uint y = (cell_coords.y & _last_cell_coord) << _cell_coord_bits;
    return IDR(x | y);
}

inline
Point2i GridLocator::get_cell_coords(IDR cell_id) const
{
    const Point2i p(cell_id & _last_cell_coord, 
                    cell_id >> _cell_coord_bits);
    return p;
}

inline
uint GridLocator::get_intersecting_cells(const Rect2& r, IDR* cell_ids, uint max_cell_ids) const
{
    return get_intersecting_cells(r.pos.x, r.pos.y, r.pos.x+r.size.x, r.pos.y+r.size.y, cell_ids, max_cell_ids);
}

inline
uint GridLocator::get_intersecting_cells(float ax, float ay, float bx, float by, IDR* cell_ids, uint max_cell_ids) const
{
    if (!max_cell_ids) return 0;

    const uint mwc = _max_world_coords - 1; // max world coord. Se asume que max_world_coords es mayor que cero y que ademas es una potencia de 2.
    uint u_ax = (ax < 0) ? 0 : ((ax >= _max_world_coords) ? mwc : uint(ax));
    uint u_ay = (ay < 0) ? 0 : ((ay >= _max_world_coords) ? mwc : uint(ay));
    uint u_bx = (bx < 0) ? 0 : ((bx >= _max_world_coords) ? mwc : uint(bx));
    uint u_by = (by < 0) ? 0 : ((by >= _max_world_coords) ? mwc : uint(by));
    
    if ((u_ax >= u_bx) || 
        (u_ay >= u_by))
    {
        // La interseccion del objeto con el mundo es nula.
        return 0;
    }
    else
    {
        const uint h = _cell_size_bits;

        Point2i a, b;
        
        a.x = (u_ax >> h);    
        a.y = (u_ay >> h);    
        b.x = (u_bx >> h) + 1;
        b.y = (u_by >> h) + 1;

        uint cell_count = 0;
        for (int y=a.y; y<b.y; ++y)
        {
            if (cell_count == max_cell_ids) break;
            for (int x=a.x; x<b.x; ++x)
            {
                cell_ids[cell_count] = IDR((y << _cell_coord_bits) | x);
                ++cell_count;
                if (cell_count == max_cell_ids) break;
            }
        }

        return cell_count;
    }
}