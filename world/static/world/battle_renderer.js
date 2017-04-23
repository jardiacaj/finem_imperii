function BattleRenderer(battle_data) {

    var zis = this;

    /* API */

    /* INTERNALS */

    zis.render_ground = function () {
        var ground = new THREE.Mesh( zis.ground_geometry, zis.ground_material );
        ground.position.x = 0;
        ground.position.z = 0;
        ground.position.y = -1;
        zis.renderer.scene.add(ground);
    };

    zis.render_turn = function (turn_num) {
        for (var contubernium_id in zis.contubernia)  {
            if (Object.prototype.hasOwnProperty.call(zis.contubernia, contubernium_id)) {
                var contubernium = zis.contubernia[contubernium_id];
                var contubernium_in_turn = contubernium.in_turn[turn_num];

                if (contubernium.mesh === undefined) {
                    var unit = zis.units[contubernium.unit_id];
                    var character = zis.characters[unit.character_id];
                    var organization = zis.organizations[character.organization_id];

                    var mesh = new THREE.Mesh( zis.contubernium_geometry, organization.material );

                    mesh.position.x = contubernium_in_turn.x_pos;
                    mesh.position.z = contubernium_in_turn.z_pos;
                    mesh.position.y = 0.5;

                    mesh.contubernium = contubernium;
                    mesh.pick_type = "contubernium";
                    contubernium.mesh = mesh;

                    zis.renderer.scene.add(mesh);
                }

            }
        }
    };

    zis.generate_organization_materials = function () {
        for (var organization_id in zis.organizations) {
            if (Object.prototype.hasOwnProperty.call(zis.organizations, organization_id)) {
                var organization = zis.organizations[organization_id];
                organization.material = new THREE.MeshLambertMaterial({
                    color: parseInt(organization.color, 16),
                    shading: THREE.SmoothShading
                });
            }
        }
    };

    /* DATA */

    zis.organizations = battle_data.organizations;
    zis.characters = battle_data.characters;
    zis.units = battle_data.units;
    zis.contubernia = battle_data.contubernia;
    zis.turn_count = battle_data.turn_count;

    /* VARS */

    zis.showing_turn = 0;

    /* MATERIALS AND GEOMETRIES */

    zis.ground_material = new THREE.MeshLambertMaterial({color: 0x1A5B07, shading: THREE.SmoothShading});
    zis.ground_geometry = new THREE.CubeGeometry(300, 2, 300);
    zis.contubernium_geometry = new THREE.CubeGeometry(0.9, 0.9, 0.9);
    zis.generate_organization_materials();

    /* CONSTRUCTION */

    zis.renderer = new BaseRenderer(40, 60, 0);
    zis.renderer.enable_rendering_helpers();
    zis.render_ground();
    zis.render_turn(zis.showing_turn);

    zis.renderer.render();
    $(document).on('click', zis.mouse_click_listener_notifier);

}
