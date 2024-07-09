#include <string>

//#include "uws/uWS.h" // uWS library

#include "utils.h"

int64 currentMSecsSinceEpoch()
{
    using namespace std::chrono;
    milliseconds ms = duration_cast< milliseconds >(
        system_clock::now().time_since_epoch()
    );
    return ms.count();
}

std::string hex_md5(const uint8_t *p_md5) 
{
	return hex_encode_buffer(p_md5, 16);
}

std::string hex_encode_buffer(const uint8_t *p_buffer, int p_len) 
{
	static const char hex[16]={'0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f'};

	std::string ret;
	char v[2]={0,0};

	for(int i=0;i<p_len;i++) {
		v[0]=hex[p_buffer[i]>>4];
		ret+=v;
		v[0]=hex[p_buffer[i]&0xF];
		ret+=v;
	}

	return ret;
}

void latin_to_utf8(const char* p_str, uint32_t p_str_size, char* p_buffer, uint32_t p_buffer_size)
{
    ERR_FAIL_COND(p_buffer_size < ((p_str_size*2)+1));

    uint32_t b_count = 0;   // buffer count

    const uint32_t ek = p_str_size;
    for (uint32_t k=0; k<ek; ++k)
    {
        const uint8_t ch = p_str[k]; /* assume that code points above 0xff are impossible since latin-1 is 8-bit */

        if (ch < 0x80) 
        {
            ERR_FAIL_COND(p_str_size >= p_buffer_size);
            p_buffer[b_count] = ch;
            ++b_count;
        }
        else 
        {
            ERR_FAIL_COND(b_count >= p_buffer_size);
            p_buffer[b_count] = (0xc0 | (ch & 0xc0) >> 6);  /* first byte, simplified since our range is only 8-bits */
            ++b_count;
            ERR_FAIL_COND(b_count >= p_buffer_size);
            p_buffer[b_count] = (0x80 | (ch & 0x3f));
            ++b_count;
        }
    }

    ERR_FAIL_COND(b_count >= p_buffer_size);
    p_buffer[b_count] = '\0';
    ++b_count;
}

int utf8_strlen(const char* str, uint str_len)
{
    int c,i,ix,q;
    for (q=0, i=0, ix=str_len; i < ix; i++, q++)
    {
        c = (unsigned char) str[i];
        if      (c>=0   && c<=127) i+=0;
        else if ((c & 0xE0) == 0xC0) i+=1;
        else if ((c & 0xF0) == 0xE0) i+=2;
        else if ((c & 0xF8) == 0xF0) i+=3;
        //else if (($c & 0xFC) == 0xF8) i+=4; // 111110bb //byte 5, unnecessary in 4 byte UTF-8
        //else if (($c & 0xFE) == 0xFC) i+=5; // 1111110b //byte 6, unnecessary in 4 byte UTF-8
        else return 0;//invalid utf8
    }
    return q;
}

void get_sunflower_points(uint n, Vector2* points)
{
    RTCHECK(points);

    const double PHI = (sqrt(5) + 1) / 2;
    const double DIV = sqrt(n - 0.5);
    const double F = 2 * Math_PI / (PHI * PHI);

    for (uint i=0; i<n; ++i)
    {
        const uint k = i + 1;
        const double r = sqrt(k - 0.5) / DIV;
        const double theta = F * k;
        Vector2& v = points[i];
        v.x = float(r * cos(theta));
        v.y = float(r * sin(theta));
    }
}

void get_random_string(char* dst, uint dst_size)
{
    for (uint i=0; i<dst_size; ++i)
    {
        dst[i] = char((rand() % 95) + 32);
    }
}

void get_random_hex_string(char* dst, uint dst_size)
{
    static const char HEXCHAR[] = { '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f' };
    for (uint i=0; i<dst_size; ++i)
    {
        dst[i] = HEXCHAR[rand() % 16];
    }
}

void get_random_bytes(ubyte* dst, uint dst_size)
{
    for (uint i=0; i<dst_size; ++i)
    {
        dst[i] = ubyte(rand() % 256);
    }
}

//uint64_t get_ticks_usec()
//{
//    // uv_hrtime devuelve nanosegundos
//    return uv_hrtime() / 1000;
//}

uint required_bits(uint number)
{
    uint r = 2;
    uint n = 0;
    for (; n<32; ++n)
    {
        if (number < r)
            break;
        r <<= 1;
    }
    return (n < 32) ? n+1 : 32;
}

