#pragma once

#include "core/json_types.h"

using nlohmann::json;

void to_json(nlohmann::json& j, const Vector2& v)
{
    j = json::array({v.x, v.y});
}

void from_json(const nlohmann::json& j, Vector2& v)
{
    v.x = j.at(0).get<float>();
    v.y = j.at(1).get<float>();
}


void to_json(nlohmann::json& j, const Point2i& v)
{
    j = json::array({v.x, v.y});
}

void from_json(const nlohmann::json& j, Point2i& v)
{
    v.x = j.at(0).get<int>();
    v.y = j.at(1).get<int>();
}