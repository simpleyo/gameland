#pragma once

#include "core/math/math_2d.h"
#include "core/json/include/json.hpp"

void to_json(nlohmann::json& j, const Vector2& v);
void from_json(const nlohmann::json& j, Vector2& v);

void to_json(nlohmann::json& j, const Point2i& v);
void from_json(const nlohmann::json& j, Point2i& v);


