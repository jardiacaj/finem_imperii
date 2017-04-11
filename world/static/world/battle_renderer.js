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

    /* DATA */

    zis.organizations = battle_data.organizations;
    zis.characters = battle_data.characters;
    zis.units = battle_data.units;
    zis.contubernia = battle_data.contubernia;
    zis.turn_count = battle_data.turn_count;

    /* VARS */

    zis.showing_turn = 0;

    /* MATERIALS AND GEOMETRIES */

    zis.ground_material = new THREE.MeshLambertMaterial({color: 0x207F07, shading: THREE.SmoothShading});
    zis.ground_geometry = new THREE.CubeGeometry(100, 2, 100);

    /* CONSTRUCTION */

    zis.renderer = new BaseRenderer();
    zis.renderer.enable_rendering_helpers();
    zis.render_ground()

    zis.renderer.render();
    $(document).on('click', zis.mouse_click_listener_notifier);

}
