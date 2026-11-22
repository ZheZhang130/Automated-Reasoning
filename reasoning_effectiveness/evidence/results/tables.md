### Development (Codex replay)

| Task | A | A/aci1 | A/aci2-s2108 | A/aci2-s2109 | A/s2109 | C | C/aci1 | C/aci2-s2108 | C/aci2-s2109 | C/s2109 | D | D/aci1 | D/aci2-s2108 | D/aci2-s2109 | D/cv2 | D/s2109 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| abc391_a | ✓ | ✓ | — | — | ✓ | ✓ | ✓ | — | — | ✓ | ✓ | ✓ | — | — | ✓ | ✓ |
| abc400_b | ✓ | ✓ | — | — | ✓ | ✓ | ✓ | — | — | ✓ | ✓ | ✓ | — | — | ✓ | ✓ |
| arc192_a | ✗ no submission (RepeatedFormatError) | ✗ 29/40 (ActionLimit) | ✗ 29/40 (Submitted) | ✗ 39/40 (Submitted) | ✗ 39/40 (Submitted) | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ 20/40 (Submitted) | ✗ no submission (RepeatedFormatError) | ✗ no submission (RepeatedFormatError) | ✗ 39/40 (Submitted) | ✗ 30/40 (ActionLimit) | ✗ no submission (RepeatedFormatError) |
| arc195_a | ✗ 39/40 (Submitted) | ✗ 37/40 (ActionLimit) | ✓ | ✗ 39/40 (Submitted) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ no submission (RepeatedFormatError) | ✗ 17/40 (ActionLimit) | ✗ 38/40 (Submitted) | ✓ | ✓ | ✗ no submission (RepeatedFormatError) |

| Metric | A | A/aci1 | A/aci2-s2108 | A/aci2-s2109 | A/s2109 | C | C/aci1 | C/aci2-s2108 | C/aci2-s2109 | C/s2109 | D | D/aci1 | D/aci2-s2108 | D/aci2-s2109 | D/cv2 | D/s2109 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| correct | 2 | 2 | 1 | 0 | 3 | 4 | 4 | 2 | 2 | 4 | 2 | 2 | 0 | 1 | 3 | 2 |
| submitted | 3 | 2 | 1 | 2 | 4 | 4 | 4 | 2 | 2 | 4 | 3 | 2 | 1 | 2 | 3 | 2 |
| candidate | 3 | 4 | 2 | 2 | 4 | 4 | 4 | 2 | 2 | 4 | 3 | 3 | 1 | 2 | 4 | 2 |
| public_final_pass | 3 | 2 | 1 | 2 | 4 | 4 | 4 | 2 | 2 | 4 | 3 | 2 | 1 | 2 | 3 | 2 |
| repeated_format_exit | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 0 | 0 | 2 |
| length_truncations | 5 | 4 | 4 | 2 | 3 | 0 | 0 | 0 | 0 | 0 | 5 | 6 | 5 | 7 | 4 | 6 |
| completion_tokens | 24431 | 27477 | 26107 | 12455 | 16657 | 3012 | 3012 | 2644 | 2050 | 2460 | 23899 | 31642 | 22241 | 41952 | 23264 | 24958 |
| local_coding_seconds | 300.8 | 341.7 | 298.4 | 155.5 | 219.8 | 75.7 | 75.6 | 51.6 | 45.4 | 69.9 | 288.1 | 375.0 | 252.2 | 475.2 | 293.6 | 293.4 |

### Provider comparison (development, API guidance)

| Task | C/api | D/api |
| --- | --- | --- |
| arc192_a | ✗ 21/40 (Submitted) | ✗ no submission (RepeatedFormatError) |

| Metric | C/api | D/api |
| --- | ---: | ---: |
| correct | 0 | 0 |
| submitted | 1 | 0 |
| candidate | 1 | 0 |
| public_final_pass | 1 | 0 |
| repeated_format_exit | 0 | 1 |
| length_truncations | 1 | 3 |
| completion_tokens | 7265 | 12288 |
| local_coding_seconds | 90.0 | 135.0 |

### MB1 Codex replay, original agent

| Task | A | C | D |
| --- | --- | --- | --- |
| abc388_g | ✗ no submission (RepeatedFormatError) | ✓ | ✗ no submission (RepeatedFormatError) |
| abc390_c | ✓ | ✓ | ✓ |
| abc392_d | ✗ 15/40 (Submitted) | ✗ 15/40 (Submitted) | ✗ 15/40 (Submitted) |
| abc394_c | ✓ | ✓ | ✓ |
| abc396_a | ✓ | ✓ | ✓ |
| abc396_d | ✓ | ✓ | ✓ |

| Metric | A | C | D |
| --- | ---: | ---: | ---: |
| correct | 4 | 5 | 4 |
| submitted | 5 | 6 | 5 |
| candidate | 5 | 6 | 5 |
| public_final_pass | 5 | 6 | 5 |
| repeated_format_exit | 1 | 0 | 1 |
| length_truncations | 3 | 0 | 4 |
| completion_tokens | 14961 | 2753 | 18226 |
| local_coding_seconds | 215.3 | 89.4 | 246.3 |

### MB2 direct API, original agent

| Task | A | C | D |
| --- | --- | --- | --- |
| abc391_e | ✗ no submission (RepeatedFormatError) | ✗ 5/40 (ActionLimit) | ✗ no submission (RepeatedFormatError) |
| abc393_d | ✗ 9/40 (RepairLimit) | ✓ | ✓ |
| abc393_e | ✓ | ✓ | ✓ |
| abc396_e | ✗ 18/40 (Submitted) | ✗ 26/40 (Submitted) | ✗ 28/40 (Submitted) |

| Metric | A | C | D |
| --- | ---: | ---: | ---: |
| correct | 1 | 2 | 2 |
| submitted | 2 | 3 | 3 |
| candidate | 3 | 4 | 3 |
| public_final_pass | 2 | 3 | 3 |
| repeated_format_exit | 1 | 0 | 1 |
| length_truncations | 5 | 1 | 3 |
| completion_tokens | 31106 | 14506 | 18108 |
| local_coding_seconds | 379.2 | 238.7 | 247.2 |

### MB1 Codex replay, aci-v2 arm

| Task | A/aci2 | C/aci2 | D/aci2 |
| --- | --- | --- | --- |
| abc388_g | ✗ no submission (RepeatedFormatError) | ✓ | ✗ no submission (RepeatedFormatError) |
| abc390_c | ✓ | ✓ | ✓ |
| abc392_d | ✗ 15/40 (Submitted) | ✗ 15/40 (Submitted) | ✗ 15/40 (Submitted) |
| abc394_c | ✓ | ✓ | ✗ 39/40 (LimitsExceeded) |
| abc396_a | ✓ | ✓ | ✓ |
| abc396_d | ✓ | ✓ | ✓ |

| Metric | A/aci2 | C/aci2 | D/aci2 |
| --- | ---: | ---: | ---: |
| correct | 4 | 5 | 3 |
| submitted | 5 | 6 | 4 |
| candidate | 5 | 6 | 5 |
| public_final_pass | 5 | 6 | 4 |
| repeated_format_exit | 1 | 0 | 1 |
| length_truncations | 3 | 0 | 4 |
| completion_tokens | 14961 | 2753 | 21998 |
| local_coding_seconds | 220.5 | 90.8 | 296.9 |

### MB2 direct API, aci-v2 arm

| Task | A/aci2 | C/aci2 | D/aci2 |
| --- | --- | --- | --- |
| abc391_e | ✗ no submission (RepeatedFormatError) | ✗ 5/40 (LimitsExceeded) | ✗ no submission (RepeatedFormatError) |
| abc393_d | ✗ 9/40 (RepairLimit) | ✓ | ✓ |
| abc393_e | ✓ | ✓ | ✓ |
| abc396_e | ✗ 22/40 (RepairLimit) | ✗ 26/40 (Submitted) | ✗ 28/40 (Submitted) |

| Metric | A/aci2 | C/aci2 | D/aci2 |
| --- | ---: | ---: | ---: |
| correct | 1 | 2 | 2 |
| submitted | 1 | 3 | 3 |
| candidate | 3 | 4 | 3 |
| public_final_pass | 1 | 3 | 3 |
| repeated_format_exit | 1 | 0 | 1 |
| length_truncations | 5 | 2 | 3 |
| completion_tokens | 39077 | 18273 | 26892 |
| local_coding_seconds | 479.6 | 249.5 | 361.1 |
