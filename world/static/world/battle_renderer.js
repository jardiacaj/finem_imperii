function BattleRenderer(battle_data) {

    var zis = this;

    /* API */

    zis.click_callback = undefined;
    zis.hover_callback = undefined;

    zis.step_back = function () {
        if (zis.showing_turn > 0) zis.showing_turn--;
        zis.animated_update();
    };

    zis.step_fwd = function () {
        if (zis.showing_turn < zis.turn_count - 1) zis.showing_turn++;
        zis.animated_update();
    };

    zis.turn_back = function () {
        zis.showing_turn = Math.max(
            zis.showing_turn - zis.battle_ticks_per_turn,
            0
        );
        zis.animated_update();
    };

    zis.turn_fwd = function () {
        zis.showing_turn = Math.min(
            zis.showing_turn + zis.battle_ticks_per_turn,
            zis.turn_count - 1
        );
        zis.animated_update();
    };

    /* INTERNALS */

    zis.render_ground = function () {
        var ground = new THREE.Mesh(zis.ground_geometry, zis.ground_material);
        ground.position.x = 0;
        ground.position.z = 0;
        ground.position.y = -1;
        zis.renderer.scene.add(ground);
    };

    zis.get_contubernium_actual_material = function (contubernium) {
        if (contubernium === zis.clicked_contubernium) {
            return zis.contubernium_material_highlighted;
        } else if (contubernium === zis.picked_contubernium) {
            return zis.contubernium_material_highlighted;
        } else {
            return zis.get_contubernium_default_material(contubernium);
        }
    };

    zis.get_contubernium_default_material = function (contubernium) {
        var unit = zis.units[contubernium.unit_id];
        var character = zis.characters[unit.character_id];
        var organization = zis.organizations[unit.organization_id];
        return organization.material;
    };

    function contubernium_scale_factor(contubernium_in_turn) {
        if (contubernium_in_turn === undefined) {return 0;}
        return Math.sqrt(contubernium_in_turn.soldiers.length) / Math.sqrt(8);
    }

    zis.add_contubernium = function (contubernium, contubernium_in_turn) {
        var material = zis.get_contubernium_default_material(contubernium);
        var mesh = new THREE.Mesh( zis.contubernium_geometry, material );

        if (contubernium_in_turn === undefined) {
            mesh.position.x = 1000;
            mesh.position.z = 1000;
        } else {
            mesh.position.x = contubernium_in_turn.x_pos;
            mesh.position.z = contubernium_in_turn.z_pos;
        }
        mesh.position.y = 0.5;

        mesh.scale.x = contubernium_scale_factor(contubernium_in_turn);
        mesh.scale.z = contubernium_scale_factor(contubernium_in_turn);

        mesh.contubernium = contubernium;
        mesh.pick_type = "contubernium";
        contubernium.mesh = mesh;

        zis.renderer.scene.add(mesh);
    };

    zis.create_attack_display = function (contubernium) {
        if (contubernium.attack_line !== undefined) {
            zis.remove_attack_display(contubernium);
        }

        var contubernium_in_turn = contubernium.in_turn[zis.showing_turn];
        var target = zis.contubernia[contubernium_in_turn.attack_target];
        var target_in_turn = target.in_turn[zis.showing_turn];
        var geometry = new THREE.Geometry();
        geometry.vertices.push(new THREE.Vector3(
            contubernium_in_turn.x_pos, 1, contubernium_in_turn.z_pos));
        geometry.vertices.push(new THREE.Vector3(
            target_in_turn.x_pos, 1, target_in_turn.z_pos));
        var line = new THREE.Line(geometry, zis.attack_line_material);
        contubernium.attack_line = line;
        zis.renderer.scene.add(line);
    };

    zis.remove_attack_display = function (contubernium) {
        if(contubernium.attack_line === undefined) return;
        zis.renderer.scene.remove(contubernium.attack_line);
        contubernium.attack_line = undefined;
    };

    zis.update_turn_counter = function () {
        $('#current_turn_display').text(zis.showing_turn);
        $('#total_turn_display').text(zis.turn_count - 1);
    };

    zis.animated_update = function () {
        for (var contubernium_id in zis.contubernia) {
            if (Object.prototype.hasOwnProperty.call(
                    zis.contubernia, contubernium_id)) {
                var contubernium = zis.contubernia[contubernium_id];
                var contubernium_in_turn = contubernium.in_turn[
                    zis.showing_turn];

                if (contubernium.mesh === undefined) {
                    zis.add_contubernium(contubernium, contubernium_in_turn);
                } else {
                    contubernium.mesh.position.x = (contubernium_in_turn ===
                        undefined ? 1000 : contubernium_in_turn.x_pos);
                    contubernium.mesh.position.z = (contubernium_in_turn ===
                        undefined ? 1000 : contubernium_in_turn.z_pos);
                    contubernium.mesh.scale.x = contubernium_scale_factor(
                        contubernium_in_turn);
                    contubernium.mesh.scale.z = contubernium_scale_factor(
                        contubernium_in_turn);
                }

                if (contubernium_in_turn &&
                        contubernium_in_turn.attack_target) {
                    zis.create_attack_display(contubernium);
                } else {
                    zis.remove_attack_display(contubernium);
                }

            }
        }
        zis.renderer.render();
        zis.update_turn_counter();
    };

    zis.generate_organization_materials = function () {
        var loader = new THREE.TextureLoader();
        zis.archer_texture = loader.load('/static/battle/icons/bow-and-arrow.png', zis.renderer.render);

        for (var organization_id in zis.organizations) {
            if (Object.prototype.hasOwnProperty.call(
                    zis.organizations, organization_id)) {
                var organization = zis.organizations[organization_id];
                organization.material = new THREE.MeshLambertMaterial({
                    color: parseInt(organization.color, 16),
                    map: zis.archer_texture,
                    transparent: true,
                });
            }
        }
    };

    zis.mouse_click_listener_notifier = function (event) {
        var previously_clicked = zis.clicked_contubernium;

        if (zis.picked_contubernium === undefined) {
            zis.clicked_contubernium = undefined;
        } else {
            zis.clicked_contubernium = zis.picked_contubernium;
            zis.clicked_contubernium.mesh.material =
                zis.get_contubernium_actual_material(zis.clicked_contubernium);
        }
        if (previously_clicked !== undefined) {
            previously_clicked.mesh.material =
                zis.get_contubernium_actual_material(previously_clicked);
        }

        zis.renderer.render();

        if (zis.click_callback) {
            if (zis.clicked_contubernium === undefined) {
                zis.click_callback(undefined);
            } else {
                zis.click_callback(zis.clicked_contubernium);
            }
        }
    };

    zis.notify_contubernium_pick = function (contubernium_three_object,
                                             mousemove_event) {
        var previously_picked = zis.picked_contubernium;

        if (contubernium_three_object === undefined) {
            zis.picked_contubernium = undefined;
        } else {
            zis.picked_contubernium = contubernium_three_object.contubernium;
            zis.picked_contubernium.mesh.material =
                zis.get_contubernium_actual_material(zis.picked_contubernium);
        }
        if (previously_picked !== undefined) {
            previously_picked.mesh.material =
                zis.get_contubernium_actual_material(previously_picked);
        }

        zis.renderer.render();

        if (zis.hover_callback) {
            if (zis.picked_contubernium === undefined) {
                zis.hover_callback(undefined);
            } else {
                zis.hover_callback(zis.picked_contubernium, mousemove_event);
            }
        }

    };

    /* DATA */

    zis.organizations = battle_data.organizations;
    zis.characters = battle_data.characters;
    zis.units = battle_data.units;
    zis.contubernia = battle_data.contubernia;
    zis.battle_ticks_per_turn = battle_data.battle_ticks_per_turn;
    zis.turn_count = battle_data.turn_count;

    /* VARS */
    zis.showing_turn =
        Math.max(zis.turn_count - 1 - zis.battle_ticks_per_turn, 0);
    zis.picked_contubernium = undefined;
    zis.clicked_contubernium = undefined;

    /* MATERIALS AND GEOMETRIES */

    zis.contubernium_material_highlighted = new THREE.MeshBasicMaterial(
        {color: 0xFFFFFF});
    zis.attack_line_material = new THREE.LineBasicMaterial({color: 0xFFFFFF});
    zis.ground_material = new THREE.MeshLambertMaterial({color: 0x1A5B07});
    zis.ground_geometry = new THREE.CubeGeometry(300, 2, 300);
    zis.contubernium_geometry = new THREE.CubeGeometry(0.9, 0.9, 0.9);

    /* CONSTRUCTION */

    zis.renderer = new BaseRenderer(40, 60, 0);
    zis.generate_organization_materials();
    zis.renderer.picking_types['contubernium'] = zis.notify_contubernium_pick;
    zis.render_ground();
    zis.animated_update();

    zis.renderer.render();
    $(zis.renderer.canvas_container).on('click',
        zis.mouse_click_listener_notifier);

}
