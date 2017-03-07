function MapRenderer(world_data) {

    var zis = this;

    /* API */

    zis.region_callback = undefined;
    zis.settlement_callback = undefined;
    zis.click_callback = undefined;

    zis.highlight_settlement = function (settlement_id) {
        settlement = zis.settlements[settlement_id];
        settlement.mesh.material = zis.settlement_material_highlighted;
        zis.render();
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
        zis.scene.add( line );
        zis.render();
    };

    /* INTERNALS */

    zis.init_camera = function () {
        zis.camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
        zis.camera.position.z = 2.5;
        zis.camera.position.x = 2.5;
        zis.camera.position.y = 12;
        zis.camera.lookAt(new THREE.Vector3( 0, 0, 0 ));
        zis.camera.aspect = window.innerWidth / window.innerHeight;
        zis.camera.updateProjectionMatrix();
    };

    zis.init_renderer = function () {
        zis.renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
        zis.renderer.setSize(window.innerWidth, window.innerHeight);
        zis.renderer.setClearColor( 0xffffff, 0);
    };

    zis.add_orbit_controls = function () {
        zis.controls = new THREE.OrbitControls(zis.camera, zis.renderer.domElement);
        zis.controls.addEventListener( 'change', zis.render );
    };

    zis.init_lighting = function () {
        zis.ambientLight = new THREE.AmbientLight(0xffffff, 0.2);
        zis.scene.add(zis.ambientLight);
        zis.directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
        zis.directionalLight.position.set(1, 1, 1).normalize();
        zis.scene.add(zis.directionalLight);
    };

    zis.render_region = function (region) {
        var mesh = new THREE.Mesh(zis.region_geometry, zis.region_materials[region.type]);
        var mat = new THREE.LineBasicMaterial( { color: 0x000000, linewidth: 1 } );
        var wireframe = new THREE.LineSegments( zis.region_edges_geometry, mat );
        mesh.add( wireframe );

        mesh.position.x = region.x_pos - 1;
        mesh.position.z = region.z_pos - 1;
        mesh.position.y = region.y_pos;

        region.mesh = mesh;
        mesh.region = region;

        zis.scene.add(mesh);
    };

    zis.render_settlement = function (settlement) {
        var region = zis.regions[settlement.tile];
        var radius = Math.log10(settlement.population) * 0.02;
        var settlement_geometry = new THREE.CylinderGeometry( radius, radius, 0.01, 16 );
        var cylinder = new THREE.Mesh( settlement_geometry, zis.settlement_material );
        cylinder.position.x = (region.x_pos - 1) - 0.5 + settlement.x_pos/100;
        cylinder.position.z = (region.z_pos - 1) - 0.5 + settlement.z_pos/100;
        cylinder.position.y = region.y_pos + 0.51;

        cylinder.settlement = settlement;
        settlement.mesh = cylinder;

        zis.scene.add(cylinder);
    };

    zis.render_region_tag = function (region) {
        var widthHalf = window.innerWidth / 2, heightHalf = window.innerHeight / 2;
        var pos = region.mesh.position.clone();
        pos.y += 0.5;
        pos.project(zis.camera);
        pos.x = ( pos.x * widthHalf ) + widthHalf;
        pos.y = -( pos.y * heightHalf ) + heightHalf;

        if (pos.x < window.innerWidth && pos.y < window.innerHeight) {
            var region_tag = document.createElement('div');
            region_tag.style.position = 'absolute';
            region_tag.style.width = "100px";
            region_tag.style.textAlign = "center";
            region_tag.style.height = 100;
            region_tag.style.background = "transparent";
            region_tag.style.fontWeight = "bold";
            region_tag.innerHTML = region.name;
            region_tag.style.top = pos.y + 'px';
            region_tag.style.left = (pos.x - 50) + 'px';
            region_tag.className = 'region_tag';
            document.body.appendChild(region_tag);
        }
    };

    zis.render_settlement_tag = function (settlement) {
        var widthHalf = window.innerWidth / 2, heightHalf = window.innerHeight / 2;
        var pos = settlement.mesh.position.clone();
        pos.z -= 0.12;
        pos.project(zis.camera);
        pos.x = ( pos.x * widthHalf ) + widthHalf;
        pos.y = -( pos.y * heightHalf ) + heightHalf;

        if (pos.x < window.innerWidth && pos.y < window.innerHeight) {
            var settlement_tag = document.createElement('div');
            settlement_tag.style.position = 'absolute';
            settlement_tag.style.width = "100px";
            settlement_tag.style.textAlign = "center";
            settlement_tag.style.height = 100;
            settlement_tag.style.background = "transparent";
            settlement_tag.innerHTML = settlement.name;
            settlement_tag.style.top = pos.y + 'px';
            settlement_tag.style.left = (pos.x - 50) + 'px';
            settlement_tag.className = 'settlement_tag';
            document.body.appendChild(settlement_tag);
        }
    };

    zis.rerender_region_tags = function () {
        $('.region_tag').remove();

        zis.camera.updateMatrixWorld();
        zis.camera.updateProjectionMatrix();

        for (var region_id in zis.regions)  {
            var region = world_data.regions[region_id];
            zis.render_region_tag(region);
        }
    };

    zis.rerender_settlement_tags = function () {
        $('.settlement_tag').remove();

        zis.camera.updateMatrixWorld();
        zis.camera.updateProjectionMatrix();

        for (var settlement_id in zis.settlements)  {
            var settlement = world_data.settlements[settlement_id];
            zis.render_settlement_tag(settlement);
        }
    };

    zis.focus_to_region = function (region_id) {
        var region = zis.regions[region_id];
        zis.camera.position.x = region.mesh.position.x;
        zis.camera.position.y = 4;
        zis.camera.position.z = region.mesh.position.z;
        zis.camera.lookAt(region.mesh.position);
    };

    zis.mouse_move_listener = function (event) {
        // it's pointless to do anything if there are no callbacks set
        if(zis.region_callback === undefined && zis.settlement_callback === undefined && zis.click_callback === undefined)
            return;
        // calculate mouse position in normalized device coordinates
        // (-1 to +1) for both components
        zis.mouse_vector.x = (event.clientX / window.innerWidth ) * 2 - 1;
        zis.mouse_vector.y = - (event.clientY / window.innerHeight) * 2 + 1;
        zis.pick();
    };

    zis.window_resize_listener = function (event) {
        zis.camera.aspect = window.innerWidth / window.innerHeight;
        zis.camera.updateProjectionMatrix();
        zis.renderer.setSize( window.innerWidth, window.innerHeight );
        zis.render();
        if(zis.region_tags_enabled) zis.rerender_region_tags();
        if(zis.settlement_tags_enabled) zis.rerender_settlement_tags();
        zis.pick();
    };

    zis.mouse_click_listener_notifier = function (event) {
        if (zis.click_callback !== undefined) {
            return zis.click_callback(zis.picked_region, zis.picked_settlement);
        }
    };

    zis.notify_region_pick = function (region) {
        if (region !== zis.picked_region) {
            zis.picked_region = region;
            if (zis.region_callback !== undefined) return zis.region_callback(region);
        }
    };

    zis.notify_settlement_pick = function (settlement) {
        if (settlement !== zis.picked_settlement) {
            zis.picked_settlement = settlement;
            if (zis.settlement_callback !== undefined) return zis.settlement_callback(settlement);
        }
    };

    zis.pick = function () {
        zis.raycaster.setFromCamera( zis.mouse_vector, zis.camera );

        // calculate objects intersecting the picking ray
        var intersects = zis.raycaster.intersectObjects( zis.scene.children );
        var region_intersected = false;
        var settlement_intersected = false;

        // notify only the first intersected element
        for ( var i = 0; i < intersects.length; i++ ) {

            var region = intersects[ i ].object.region;
            if (region !== undefined && !region_intersected) {
                zis.notify_region_pick(region);
                region_intersected = true;
            }
            var settlement = intersects[ i ].object.settlement;
            if (settlement !== undefined && !settlement_intersected) {
                zis.notify_settlement_pick(settlement);
                settlement_intersected = true;
            }

        }

        if (!settlement_intersected) zis.notify_settlement_pick(undefined);
        if (!region_intersected) zis.notify_region_pick(undefined);
    };

    zis.render = function () {
        zis.renderer.render(zis.scene, zis.camera);
    };

    /* VARS */

    zis.regions = world_data.regions;
    zis.settlements = world_data.settlements;

    zis.travel_line_material = new THREE.LineBasicMaterial({color: 0x801919, linewidth: 3});
    zis.region_geometry = new THREE.CubeGeometry(1, 1, 1);
    zis.region_edges_geometry = new THREE.EdgesGeometry( zis.region_geometry );
    zis.region_materials = {
        "plains": new THREE.MeshLambertMaterial({color: 0x90CD00, shading: THREE.SmoothShading}),
        "forest": new THREE.MeshLambertMaterial({color: 0x207F07, shading: THREE.SmoothShading}),
        "shore": new THREE.MeshLambertMaterial({color: 0x0D81CD, shading: THREE.SmoothShading}),
        "deepsea": new THREE.MeshLambertMaterial({color: 0x000E85, shading: THREE.SmoothShading}),
        "mountain": new THREE.MeshLambertMaterial({color: 0x837D71, shading: THREE.SmoothShading}),
    };
    zis.settlement_material_highlighted = new THREE.MeshBasicMaterial( {color: 0xFFFFFF} );
    zis.settlement_material = new THREE.MeshBasicMaterial( {color: 0x000000} );

    zis.picked_region = undefined;
    zis.picked_settlement = undefined;

    zis.region_tags_enabled = false;
    zis.settlement_tags_enabled = false;

    /* CONSTRUCTION */

    zis.canvas_container = document.createElement( 'div' );
    document.body.appendChild( zis.canvas_container );

    zis.scene = new THREE.Scene();
    zis.init_camera();
    zis.init_renderer();
    zis.init_lighting();
    zis.raycaster = new THREE.Raycaster();
    zis.mouse_vector = new THREE.Vector2();

    zis.canvas_container.appendChild(zis.renderer.domElement);

    $(window).on('resize', zis.window_resize_listener);
    $(document).on('mousemove', zis.mouse_move_listener);
    $(document).on('click', zis.mouse_click_listener_notifier);

    for (var region_id in zis.regions)  {
        var region = world_data.regions[region_id];
        zis.render_region(region);
    }

    for (var settlement_id in zis.settlements)  {
        var settlement = world_data.settlements[settlement_id];
        zis.render_settlement(settlement);
    }

    zis.render();

}