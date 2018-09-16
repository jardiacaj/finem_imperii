function MapRenderer(world_data) {

    var zis = this;

    /* API */

    zis.region_callback = undefined;
    zis.settlement_callback = undefined;
    zis.click_callback = undefined;

    zis.highlight_settlement = function (settlement_id) {
        settlement = zis.settlements[settlement_id];
        settlement.mesh.material = zis.settlement_material_highlighted;
        zis.renderer.render();
    };

    zis.enable_region_tags = function () {
        zis.region_tags_enabled = true;
        zis.rerender_region_tags()
    };

    zis.enable_settlement_tags = function () {
        zis.settlement_tags_enabled = true;
        zis.rerender_settlement_tags()
    };

    zis.add_travel_line = function (source_settlement_id, target_settlement_id) {
        var source_settlement = zis.settlements[source_settlement_id];
        var target_settlement = zis.settlements[target_settlement_id];

        var geometry = new THREE.Geometry();
        geometry.vertices.push(source_settlement.mesh.position, target_settlement.mesh.position);

        var line = new THREE.Line( geometry, zis.travel_line_material );
        zis.renderer.scene.add( line );
        zis.renderer.render();
    };

    zis.link_click_to_view_callback = function (region, settlement) {
        if (region !== undefined)
            window.parent.location = '/tile/' + region.region.id;
    };

    /* WARNING: Ugly code ahead */
    zis.add_political_markings = function () {
        for (var region_id in zis.regions)  {
            if (Object.prototype.hasOwnProperty.call(zis.regions, region_id)) {
                var region = world_data.regions[region_id];
                var organization = zis.organizations[region.controlled_by];
                if (organization.barbaric) continue;

                var geometry = new THREE.PlaneGeometry(1, 0.02);

                var mesh = new THREE.Mesh( geometry, organization.political_marking_material );

                mesh.position.x = region.x_pos - 1;
                mesh.position.z = region.z_pos - 0.51;
                mesh.position.y = region.y_pos + 0.51;

                mesh.rotateX(-Math.PI/2);

                zis.renderer.scene.add(mesh);

                mesh = new THREE.Mesh( geometry, organization.political_marking_material );

                mesh.position.x = region.x_pos - 1;
                mesh.position.z = region.z_pos - 1.49;
                mesh.position.y = region.y_pos + 0.51;

                mesh.rotateX(-Math.PI/2);

                zis.renderer.scene.add(mesh);

                geometry = new THREE.PlaneGeometry(0.02, 1);

                mesh = new THREE.Mesh( geometry, organization.political_marking_material );

                mesh.position.x = region.x_pos - 0.51;
                mesh.position.z = region.z_pos - 1;
                mesh.position.y = region.y_pos + 0.51;

                mesh.rotateX(-Math.PI/2);

                zis.renderer.scene.add(mesh);

                mesh = new THREE.Mesh( geometry, organization.political_marking_material );

                mesh.position.x = region.x_pos - 1.49;
                mesh.position.z = region.z_pos - 1;
                mesh.position.y = region.y_pos + 0.51;

                mesh.rotateX(-Math.PI/2);

                zis.renderer.scene.add(mesh);
            }
        }
        zis.renderer.render();
    };

    /* INTERNALS */

    zis.mouse_click_listener_notifier = function (event) {
        if (zis.click_callback !== undefined) {
            return zis.click_callback(zis.picked_region, zis.picked_settlement);
        }
    };

    zis.notify_region_pick = function (region) {
        zis.picked_region = region;
        if (zis.region_callback !== undefined) return zis.region_callback(region);
    };

    zis.notify_settlement_pick = function (settlement) {
        zis.picked_settlement = settlement;
        if (zis.settlement_callback !== undefined) return zis.settlement_callback(settlement);
    };

    zis.render_region = function (region) {
        var mesh = new THREE.Mesh(zis.region_geometry, zis.region_materials[region.type]);
        var mat = new THREE.LineBasicMaterial( { color: 0x000000, linewidth: 1 } );
        var wireframe = new THREE.LineSegments( zis.region_edges_geometry, mat );
        mesh.add( wireframe );

        mesh.position.x = region.x_pos - 1;
        mesh.position.z = region.z_pos - 1;
        mesh.position.y = region.y_pos;

        mesh.region = region;
        mesh.pick_type = "region";
        region.mesh = mesh;

        zis.renderer.scene.add(mesh);
    };

    zis.render_settlement = function (settlement) {
        var region = zis.regions[settlement.tile];
        var organization = zis.organizations[region.controlled_by];
        var radius = Math.sqrt(settlement.population) * 0.001;
        var settlement_geometry = new THREE.CylinderGeometry( radius, radius, 0.01, 16 );
        var cylinder = new THREE.Mesh( settlement_geometry, organization.settlement_material );
        cylinder.position.x = (region.x_pos - 1) - 0.5 + settlement.x_pos/100;
        cylinder.position.z = (region.z_pos - 1) - 0.5 + settlement.z_pos/100;
        cylinder.position.y = region.y_pos + 0.51;

        cylinder.settlement = settlement;
        cylinder.pick_type = "settlement";
        settlement.mesh = cylinder;

        zis.renderer.scene.add(cylinder);
    };

    zis.render_region_tag = function (region) {
        var pos = region.mesh.position.clone();
        pos.y += 0.5;
        zis.renderer.unproject(pos);
        pos.x -= 75;
        if (pos.x < window.innerWidth && pos.y < window.innerHeight) {
            zis.create_tag_dom_element(pos, region.name, 'region_tag');
        }
    };

    zis.render_settlement_tag = function (settlement) {
        var pos = settlement.mesh.position.clone();
        pos.z -= 0.12;
        zis.renderer.unproject(pos);
        pos.x -= 50;
        if (pos.x < window.innerWidth && pos.y < window.innerHeight) {
            zis.create_tag_dom_element(pos, settlement.name, 'settlement_tag');
        }
    };

    zis.create_tag_dom_element = function (pos, html_content, className) {
        var tag_element = document.createElement('div');
        tag_element.innerHTML = html_content;
        tag_element.style.top = pos.y + 'px';
        tag_element.style.left = pos.x + 'px';
        tag_element.className = className;
        document.body.appendChild(tag_element);
    };

    zis.rerender_region_tags = function () {
        $('.region_tag').remove();

        zis.renderer.camera.updateMatrixWorld();
        zis.renderer.camera.updateProjectionMatrix();

        for (var region_id in zis.regions)  {
            if (Object.prototype.hasOwnProperty.call(zis.regions, region_id)) {
                var region = world_data.regions[region_id];
                if (region['type'] !== "shore" && region['type'] !== "deepsea") {
                    zis.render_region_tag(region);
                }
            }
        }
    };

    zis.rerender_settlement_tags = function () {
        $('.settlement_tag').remove();

        zis.renderer.camera.updateMatrixWorld();
        zis.renderer.camera.updateProjectionMatrix();

        for (var settlement_id in zis.settlements)  {
            if (Object.prototype.hasOwnProperty.call(zis.settlements, settlement_id)) {
                var settlement = world_data.settlements[settlement_id];
                zis.render_settlement_tag(settlement);
            }
        }
    };

    zis.focus_to_region = function (region_id) {
        var region = zis.regions[region_id];
        zis.renderer.camera.position.x = region.mesh.position.x;
        zis.renderer.camera.position.y = 5;
        zis.renderer.camera.position.z = region.mesh.position.z;
        zis.renderer.camera.lookAt(region.mesh.position);
    };

    /* VARS */

    zis.regions = world_data.regions;
    zis.settlements = world_data.settlements;
    zis.organizations = world_data.organizations;

    zis.picked_region = undefined;
    zis.picked_settlement = undefined;

    zis.travel_line_material = new THREE.LineBasicMaterial({color: 0x801919, linewidth: 3});
    zis.region_geometry = new THREE.CubeGeometry(1, 1, 1);
    zis.region_edges_geometry = new THREE.EdgesGeometry( zis.region_geometry );
    zis.region_materials = {
        "plains": new THREE.MeshLambertMaterial({color: 0x7D802A}),
        "forest": new THREE.MeshLambertMaterial({color: 0x0A5906}),
        "shore": new THREE.MeshLambertMaterial({color: 0x0D3E6C}),
        "deepsea": new THREE.MeshLambertMaterial({color: 0x000E59}),
        "mountain": new THREE.MeshLambertMaterial({color: 0x5C564A})
    };
    zis.settlement_material_highlighted = new THREE.MeshBasicMaterial( {color: 0xFFFFFF} );

    zis.region_tags_enabled = false;
    zis.settlement_tags_enabled = false;

    /* CONSTRUCTION */
    zis.renderer = new BaseRenderer(2.5, 12, 2.5);
    zis.renderer.picking_types['settlement'] = zis.notify_settlement_pick;
    zis.renderer.picking_types['region'] = zis.notify_region_pick;

    for (var organization_id in zis.organizations) {
        if (Object.prototype.hasOwnProperty.call(zis.organizations, organization_id)) {
            var organization = zis.organizations[organization_id];
            organization.settlement_material = new THREE.MeshBasicMaterial({color: parseInt(organization.color, 16)});
            organization.political_marking_material = new THREE.MeshBasicMaterial({
                color: parseInt(organization.color, 16),
                transparent: true,
                opacity: 1
            });
        }
    }

    for (var region_id in zis.regions)  {
        if (Object.prototype.hasOwnProperty.call(zis.regions, region_id)) {
            var region = zis.regions[region_id];
            zis.render_region(region);
        }
    }

    for (var settlement_id in zis.settlements)  {
        if (Object.prototype.hasOwnProperty.call(zis.settlements, settlement_id)) {
            var settlement = zis.settlements[settlement_id];
            zis.render_settlement(settlement);
        }
    }

    zis.renderer.render();
    $(zis.renderer.canvas_container).on('click', zis.mouse_click_listener_notifier);

}
