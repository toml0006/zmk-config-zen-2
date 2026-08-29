# Generated release artifacts

Run `keycap_makerworld` inside Fusion to generate
`MakerWorld_Parametric_Choc_Keycap.f3d` in this directory.

The generated F3D opens standing on a long side edge with the model seated on
the XY build plane. Keep this orientation when generating or slicing custom
parameter combinations; do not place the cap flat on its underside.

Do not treat a Python-only change as a release. Regenerate the F3D, exercise
the full parameter validation matrix, and test it privately in MakerWorld.

`print_profiles/` contains one sliced Bambu Studio 3MF project for each of the
12 catalog configurations and one all-in-one sampler with all 12 objects on a
single plate. Rebuild and validate them with
`../print_profiles/build_bambu_3mf_profiles.py`. They target an A1 mini with a
0.2 mm nozzle and Bambu PLA Matte, use 100% infill and normal automatic
supports, and are oriented standing on edge. Each project carries a matching
profile image and plate thumbnail. Use a freshly washed, fingerprint-free
build plate. Use the 12-configuration sampler as the MakerWorld print profile.
