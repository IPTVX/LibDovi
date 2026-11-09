// Exercises the shipped C ABI, including serialization after mapping changes.
#include <dovi.h>
#include <assert.h>
#include <math.h>
#include <stdio.h>

int main(void) {
    const DoviRpuOpaqueList *list = dovi_generate_from_json("{\"cm_version\": \"V29\", \"length\": 1, \"level6\": {\"max_display_mastering_luminance\": 1000, \"min_display_mastering_luminance\": 1, \"max_content_light_level\": 1000, \"max_frame_average_light_level\": 400}, \"shots\": [{\"start\": 0, \"duration\": 1, \"metadata_blocks\": []}]}");
    if (list && list->error && list->error[0]) fprintf(stderr, "%s\n", list->error);
    assert(list && list->len == 1);
    DoviRpuOpaque *rpu = list->list[0];
    const uint16_t pivots[] = {0, 512, 1023};
    const double coefficients[] = {0, 1, 0, 0, 1, 0};
    assert(dovi_rpu_set_polynomial_mapping(rpu, 0, pivots, 3, coefficients) == 0);
    const DoviData *encoded = dovi_write_rpu(rpu);
    assert(encoded && encoded->len > 0);
    DoviRpuOpaque *roundtrip = dovi_parse_rpu(encoded->data, encoded->len);
    assert(roundtrip && (!dovi_rpu_get_error(roundtrip) || !dovi_rpu_get_error(roundtrip)[0]));
    const DoviRpuDataMapping *mapping = dovi_rpu_get_data_mapping(roundtrip);
    assert(mapping && mapping->curves[0].mapping_idc == 0);
    assert(mapping->curves[0].num_pivots_minus2 == 1);
    assert(mapping->curves[0].pivots.len == 3);
    assert(mapping->curves[0].pivots.data[2] == 511);
    assert(mapping->curves[0].polynomial->poly_coef_int.len == 2);
    assert(mapping->curves[0].polynomial->poly_coef_int.list[0]->data[1] == 1);
    dovi_rpu_free_data_mapping(mapping);
    dovi_rpu_free(roundtrip);
    dovi_data_free(encoded);
    puts("PASS polynomial mapping serialized and reparsed with matching coefficients/pivots");
    assert(dovi_rpu_set_polynomial_mapping(NULL, 0, pivots, 3, coefficients) == -1);
    assert(dovi_rpu_set_polynomial_mapping(rpu, 3, pivots, 3, coefficients) == -1);
    assert(dovi_rpu_set_polynomial_mapping(rpu, 0, pivots, 1, coefficients) == -1);
    const uint16_t descending[] = {1023, 0};
    assert(dovi_rpu_set_polynomial_mapping(rpu, 0, descending, 2, coefficients) == -1);
    const double invalid[] = {NAN, 1, 0};
    assert(dovi_rpu_set_polynomial_mapping(rpu, 0, pivots, 2, invalid) == -1);
    puts("PASS null/component/count/order/nonfinite rejection cases");
    dovi_rpu_list_free(list);
    return 0;
}
