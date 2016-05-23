package org.mskcc.oncotree.api;

import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;
import io.swagger.annotations.ApiResponses;
import org.mskcc.oncotree.model.MainTypeResp;
import org.mskcc.oncotree.model.MainTypesResp;
import org.mskcc.oncotree.model.Meta;
import org.mskcc.oncotree.utils.MainTypesUtil;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;

import static org.springframework.http.MediaType.APPLICATION_JSON_VALUE;

@Controller
@RequestMapping(value = "/api/mainTypes", produces = {APPLICATION_JSON_VALUE})
@Api(value = "/mainTypes", description = "the mainTypes API")
@javax.annotation.Generated(value = "class io.swagger.codegen.languages.SpringMVCServerCodegen", date = "2016-04-25T21:05:12.544Z")
public class MainTypesApi {


    @ApiOperation(value = "Return all available main tumor types.", notes = "", response = MainTypesResp.class)
    @ApiResponses(value = {
        @io.swagger.annotations.ApiResponse(code = 200, message = "Nested tumor types object.")})
    @RequestMapping(value = "",
        produces = {"application/json"},
        method = RequestMethod.GET)
    public ResponseEntity<MainTypesResp> mainTypesGet(
        @ApiParam(value = "The callback function name. This has to be used with dataType JSONP.")
        @RequestParam(value = "callback", required = false) String callback
    )
        throws NotFoundException {
        MainTypesResp resp = new MainTypesResp();

        Meta meta = new Meta();
        meta.setCode(200);
        resp.setMeta(meta);

        resp.setData(MainTypesUtil.getMainTypes());

        return new ResponseEntity<MainTypesResp>(resp, HttpStatus.OK);
    }


    @ApiOperation(value = "Get main type by using numerical unique ID", notes = "", response = MainTypeResp.class)
    @ApiResponses(value = {
        @io.swagger.annotations.ApiResponse(code = 200, message = "OK")})
    @RequestMapping(value = "/{id}",
        produces = {"application/json"},
        method = RequestMethod.GET)
    public ResponseEntity<MainTypeResp> mainTypesIdGet(
        @ApiParam(value = "The numerical ID of the desired tumor type", required = true) @PathVariable("id") String id,
        @ApiParam(value = "The callback function name. This has to be used with dataType JSONP.") @RequestParam(value = "callback", required = false) String callback
    )
        throws NotFoundException {
        MainTypeResp resp = new MainTypeResp();

        Meta meta = new Meta();
        meta.setCode(200);
        resp.setMeta(meta);

        resp.setData(MainTypesUtil.getMainType(Integer.getInteger(id)));

        return new ResponseEntity<MainTypeResp>(resp, HttpStatus.OK);
    }


}